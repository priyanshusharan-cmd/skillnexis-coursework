import time

import jwt
import pytest
from fastapi.testclient import TestClient

from blogly.app import create_app
from blogly.ratelimit import TokenBucket
from blogly.security import create_token, hash_password, verify_password

SECRET = "test-secret-" + "x" * 32


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(db_path=str(tmp_path / "t.db"), secret=SECRET, rate_per_min=1000, login_per_min=1000))


def signup(c, name="priya", pw="correct-horse-1"):
    assert c.post("/auth/register", json={"username": name, "password": pw}).status_code == 201
    tok = c.post("/auth/login", json={"username": name, "password": pw}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


# ---------------------------------------------------------------- auth
def test_register_login_me(client):
    r = client.post("/auth/register", json={"username": "priya", "password": "correct-horse-1"})
    assert r.status_code == 201 and r.json()["username"] == "priya" and "password_hash" not in r.json()
    tok = client.post("/auth/login", json={"username": "priya", "password": "correct-horse-1"}).json()
    assert tok["token_type"] == "bearer" and tok["expires_in"] == 3600
    me = client.get("/users/me", headers={"Authorization": "Bearer " + tok["access_token"]})
    assert me.status_code == 200 and me.json()["username"] == "priya"


def test_duplicate_username_is_case_insensitive(client):
    signup(client, "Priya")
    assert client.post("/auth/register", json={"username": "priya", "password": "another-pass-1"}).status_code == 409


@pytest.mark.parametrize("body", [
    {"username": "ab", "password": "long-enough-1"},          # username too short
    {"username": "bad name", "password": "long-enough-1"},    # space in username
    {"username": "priya", "password": "short"},                # password under 8
    {"username": "priya", "password": "é" * 40},               # 80 bytes > 72
    {"username": "priya", "password": " padded-pass "},        # leading/trailing space
    {"username": "priya"},                                     # missing field
])
def test_register_validation(client, body):
    assert client.post("/auth/register", json=body).status_code == 422


def test_login_failure_does_not_reveal_which_part_was_wrong(client):
    signup(client)
    wrong_pw = client.post("/auth/login", json={"username": "priya", "password": "wrong-password"})
    no_user = client.post("/auth/login", json={"username": "nobody", "password": "wrong-password"})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json() == no_user.json() == {"detail": "Incorrect username or password"}


@pytest.mark.parametrize("make_token,detail", [
    (lambda: None, "Not authenticated"),
    (lambda: "garbage", "Invalid token"),
    (lambda: jwt.encode({"sub": "1", "iat": 0, "exp": int(time.time()) + 60}, "another-secret-" + "y" * 32, algorithm="HS256"), "Invalid token"),
    (lambda: jwt.encode({"sub": "1", "iat": 0, "exp": 1}, SECRET, algorithm="HS256"), "Token expired"),
    (lambda: jwt.encode({"sub": "1", "iat": 0, "exp": int(time.time()) + 60}, SECRET + "z", algorithm="HS384"), "Invalid token"),  # alg not allowed
    (lambda: create_token(999, SECRET), "User no longer exists"),
])
def test_bad_tokens_are_rejected(client, make_token, detail):
    tok = make_token()
    headers = {"Authorization": f"Bearer {tok}"} if tok else {}
    r = client.post("/posts", json={"title": "t", "body": "b"}, headers=headers)
    assert r.status_code == 401 and r.json()["detail"] == detail


def test_password_hashing_is_salted_and_verifies():
    a, b = hash_password("pw-123456"), hash_password("pw-123456")
    assert a != b and verify_password("pw-123456", a) and not verify_password("pw-1234567", a)
    assert not verify_password("x", "not-a-hash") and not verify_password("x", "md5$a$b")


def test_weak_or_missing_secret_refuses_to_start(tmp_path, monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="set JWT_SECRET"):
        create_app(db_path=str(tmp_path / "x.db"))
    with pytest.raises(RuntimeError, match="at least 32"):
        create_app(db_path=str(tmp_path / "x.db"), secret="short")


# ---------------------------------------------------------------- posts CRUD + ownership
def test_post_crud_and_ownership(client):
    priya, arjun = signup(client, "priya"), signup(client, "arjun")
    r = client.post("/posts", json={"title": "  Hello  ", "body": "First post"}, headers=priya)
    assert r.status_code == 201
    post = r.json()
    assert post["title"] == "Hello" and post["author"] == "priya" and post["likes"] == post["comments"] == 0
    pid = post["id"]
    assert client.get(f"/posts/{pid}").json()["body"] == "First post"
    assert client.patch(f"/posts/{pid}", json={"title": "Hijack"}, headers=arjun).status_code == 403
    r = client.patch(f"/posts/{pid}", json={"body": "Edited"}, headers=priya)
    assert r.status_code == 200 and r.json()["body"] == "Edited" and r.json()["title"] == "Hello" and r.json()["updated_at"]
    assert client.patch(f"/posts/{pid}", json={}, headers=priya).status_code == 422
    assert client.delete(f"/posts/{pid}", headers=arjun).status_code == 403
    assert client.delete(f"/posts/{pid}", headers=priya).status_code == 204
    assert client.get(f"/posts/{pid}").status_code == 404


@pytest.mark.parametrize("body", [{"title": "", "body": "x"}, {"title": "   ", "body": "x"}, {"title": "x" * 201, "body": "x"}, {"title": "x", "body": "y" * 10_001}, {"title": "x"}])
def test_post_validation(client, body):
    assert client.post("/posts", json=body, headers=signup(client)).status_code == 422


def test_unknown_post_is_404_everywhere(client):
    h = signup(client)
    for method, path, kw in [("get", "/posts/9", {}), ("patch", "/posts/9", {"json": {"title": "x"}}), ("delete", "/posts/9", {}),
                             ("get", "/posts/9/comments", {}), ("post", "/posts/9/comments", {"json": {"body": "x"}}),
                             ("put", "/posts/9/like", {}), ("delete", "/posts/9/like", {}), ("delete", "/comments/9", {})]:
        assert getattr(client, method)(path, headers=h, **kw).status_code == 404, (method, path)


# ---------------------------------------------------------------- pagination + search
def test_pagination_newest_first_and_metadata(client):
    h = signup(client)
    for i in range(23):
        client.post("/posts", json={"title": f"Post {i}", "body": "text"}, headers=h)
    p1 = client.get("/posts", params={"page": 1, "page_size": 10}).json()
    p3 = client.get("/posts", params={"page": 3, "page_size": 10}).json()
    assert (p1["total"], p1["pages"], len(p1["items"]), p1["items"][0]["title"]) == (23, 3, 10, "Post 22")
    assert len(p3["items"]) == 3 and p3["items"][-1]["title"] == "Post 0"
    assert client.get("/posts", params={"page": 9}).json()["items"] == []
    for bad in ({"page": 0}, {"page_size": 51}, {"page_size": 0}):
        assert client.get("/posts", params=bad).status_code == 422


def test_search_title_body_author_and_wildcards_are_literal(client):
    a, b = signup(client, "priya"), signup(client, "arjun")
    client.post("/posts", json={"title": "Caching 101", "body": "Redis basics"}, headers=a)
    client.post("/posts", json={"title": "Queues", "body": "Use caching wisely"}, headers=b)
    client.post("/posts", json={"title": "Discount 100%", "body": "sale"}, headers=b)
    def titles(**q):
        return sorted(p["title"] for p in client.get("/posts", params=q).json()["items"])

    assert titles(q="caching") == ["Caching 101", "Queues"]
    assert titles(q="caching", author="arjun") == ["Queues"]
    assert titles(author="priya") == ["Caching 101"]
    assert titles(q="%") == ["Discount 100%"]   # % is matched literally, not as "everything"
    assert titles(q="_") == []


# ---------------------------------------------------------------- comments + likes
def test_comments_paginated_and_delete_rules(client):
    owner, alice, bob = signup(client, "owner"), signup(client, "alice"), signup(client, "bob")
    pid = client.post("/posts", json={"title": "T", "body": "B"}, headers=owner).json()["id"]
    ids = [client.post(f"/posts/{pid}/comments", json={"body": f"c{i}"}, headers=alice).json()["id"] for i in range(3)]
    page = client.get(f"/posts/{pid}/comments", params={"page_size": 2}).json()
    assert [c["body"] for c in page["items"]] == ["c0", "c1"] and page["pages"] == 2 and page["items"][0]["author"] == "alice"
    assert client.post(f"/posts/{pid}/comments", json={"body": "  "}, headers=bob).status_code == 422
    assert client.delete(f"/comments/{ids[0]}", headers=bob).status_code == 403     # stranger
    assert client.delete(f"/comments/{ids[0]}", headers=alice).status_code == 204   # comment author
    assert client.delete(f"/comments/{ids[1]}", headers=owner).status_code == 204   # post author moderates
    assert client.get(f"/posts/{pid}").json()["comments"] == 1


def test_likes_are_idempotent_and_counted(client):
    a, b = signup(client, "a_user"), signup(client, "b_user")
    pid = client.post("/posts", json={"title": "T", "body": "B"}, headers=a).json()["id"]
    for _ in range(3):
        assert client.put(f"/posts/{pid}/like", headers=b).status_code == 204
    client.put(f"/posts/{pid}/like", headers=a)
    assert client.get(f"/posts/{pid}").json()["likes"] == 2
    client.delete(f"/posts/{pid}/like", headers=b)
    client.delete(f"/posts/{pid}/like", headers=b)  # unliking twice is fine
    assert client.get(f"/posts/{pid}").json()["likes"] == 1
    assert client.put(f"/posts/{pid}/like").status_code == 401


def test_deleting_a_post_removes_its_comments_and_likes(client):
    h = signup(client)
    pid = client.post("/posts", json={"title": "T", "body": "B"}, headers=h).json()["id"]
    cid = client.post(f"/posts/{pid}/comments", json={"body": "c"}, headers=h).json()["id"]
    client.put(f"/posts/{pid}/like", headers=h)
    client.delete(f"/posts/{pid}", headers=h)
    assert client.delete(f"/comments/{cid}", headers=h).status_code == 404


# ---------------------------------------------------------------- rate limiting
def test_login_rate_limit_returns_429_with_retry_after(tmp_path):
    c = TestClient(create_app(db_path=str(tmp_path / "r.db"), secret=SECRET, rate_per_min=1000, login_per_min=3))
    codes = [c.post("/auth/login", json={"username": "nobody", "password": "wrong-password"}).status_code for _ in range(5)]
    assert codes == [401, 401, 401, 429, 429]
    r = c.post("/auth/login", json={"username": "nobody", "password": "wrong-password"})
    assert int(r.headers["Retry-After"]) >= 1 and r.headers["X-RateLimit-Remaining"] == "0"
    assert c.get("/health").status_code == 200  # health is never limited


def test_general_limit_is_per_user_not_shared(tmp_path):
    c = TestClient(create_app(db_path=str(tmp_path / "r.db"), secret=SECRET, rate_per_min=4, login_per_min=100))
    a, b = signup(c, "a_user"), signup(c, "b_user")
    assert [c.get("/users/me", headers=a).status_code for _ in range(5)] == [200, 200, 200, 200, 429]
    assert c.get("/users/me", headers=b).status_code == 200  # b has its own bucket
    assert c.get("/posts").headers["X-RateLimit-Limit"] == "4"


def test_token_bucket_refills_over_time_and_prunes():
    now = [0.0]
    tb = TokenBucket(capacity=2, refill_per_second=1, clock=lambda: now[0])
    assert [tb.take("k")[0] for _ in range(3)] == [True, True, False]
    assert tb.take("k")[2] == 1  # retry after ~1 s
    now[0] = 1.0
    assert tb.take("k")[0] is True
    now[0] = 10_000
    tb.prune(idle_seconds=60)
    assert tb._buckets == {}


def test_openapi_documents_every_endpoint(client):
    spec = client.get("/openapi.json").json()
    paths = {(m.upper(), p) for p, ops in spec["paths"].items() for m in ops}
    assert {("POST", "/auth/register"), ("POST", "/auth/login"), ("GET", "/users/me"), ("GET", "/posts"), ("POST", "/posts"),
            ("GET", "/posts/{post_id}"), ("PATCH", "/posts/{post_id}"), ("DELETE", "/posts/{post_id}"),
            ("GET", "/posts/{post_id}/comments"), ("POST", "/posts/{post_id}/comments"), ("DELETE", "/comments/{comment_id}"),
            ("PUT", "/posts/{post_id}/like"), ("DELETE", "/posts/{post_id}/like")} <= paths
    assert "HTTPBearer" in spec["components"]["securitySchemes"]
    assert client.get("/docs").status_code == 200
