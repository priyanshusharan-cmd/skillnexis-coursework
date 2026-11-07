"""API tests: the happy paths plus every error path the API promises.   pytest -q api/tests"""
import io, os, sys
import numpy as np, pytest
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["RATE_LIMIT_PER_MIN"] = "1000"
from fastapi.testclient import TestClient
from api import main
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "week-2", "src")); from cifar_data import load
c = TestClient(main.app); _, _, XT, YT = load()
def png(arr, fmt="PNG"):
    b = io.BytesIO(); Image.fromarray(arr).save(b, fmt); return b.getvalue()
def test_health_and_model():
    assert c.get("/health").json()["model_loaded"] is True
    m = c.get("/model").json(); assert m["classes"][0] == "airplane" and m["input"] == [32, 32, 3]
def test_predict_real_cifar_images():
    hits = 0
    for k in range(40):
        r = c.post("/predict", files={"file": (f"{k}.png", png(XT[k]), "image/png")}); assert r.status_code == 200
        j = r.json(); hits += j["label"] == main.CLASSES[YT[k]]; assert len(j["top_k"]) == 3 and abs(sum(t["probability"] for t in j["top_k"])) <= 1.0001
    assert hits >= 32, hits                          # the model is ~91 % accurate
    assert "X-Request-ID" in r.headers and "X-Process-Time-ms" in r.headers
def test_larger_jpeg_is_resized():
    big = np.asarray(Image.fromarray(XT[3]).resize((400, 300))); r = c.post("/predict?top_k=5", files={"file": ("big.jpg", png(big, "JPEG"), "image/jpeg")})
    assert r.status_code == 200 and len(r.json()["top_k"]) == 5
@pytest.mark.parametrize("files,status,code", [
    ({"file": ("notes.txt", b"hello", "text/plain")}, 415, "unsupported_media_type"),
    ({"file": ("empty.png", b"", "image/png")}, 400, "empty_file"),
    ({"file": ("fake.png", b"\x89PNG\r\n\x1a\n" + b"garbage" * 20, "image/png")}, 422, "unreadable_image"),
    ({"file": ("huge.png", b"\x89PNG" + b"0" * (5 * 1024 * 1024 + 10), "image/png")}, 413, "file_too_large"),
    ({"file": ("tiny.png", None, "image/png")}, 422, "image_too_small"),
])
def test_errors(files, status, code):
    if files["file"][1] is None: files = {"file": ("tiny.png", png(np.zeros((4, 4, 3), np.uint8)), "image/png")}
    r = c.post("/predict", files=files); j = r.json()
    assert r.status_code == status and j["error"]["code"] == code and j["error"]["request_id"], j
def test_truncated_png():
    data = png(XT[0]); r = c.post("/predict", files={"file": ("cut.png", data[: len(data) // 2], "image/png")}); assert r.status_code == 422
def test_missing_file_and_bad_param():
    assert c.post("/predict").json()["error"]["code"] == "missing_file"
    r = c.post("/predict?top_k=50", files={"file": ("a.png", png(XT[0]), "image/png")}); assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_request"
def test_batch_partial_failure():
    files = [("files", ("a.png", png(XT[0]), "image/png")), ("files", ("b.txt", b"x", "text/plain")), ("files", ("c.png", png(XT[1]), "image/png"))]
    j = c.post("/predict/batch", files=files).json(); assert j["count"] == 3 and j["succeeded"] == 2 and j["results"][1]["error"]["code"] == "unsupported_media_type"
    assert c.post("/predict/batch", files=[("files", (f"{k}.png", png(XT[k]), "image/png")) for k in range(17)]).status_code == 413
def test_rate_limit():
    main.RATE = 3; main.HITS.clear()
    codes = [c.post("/predict", files={"file": ("a.png", png(XT[0]), "image/png")}).status_code for _ in range(5)]
    main.RATE = 1000; main.HITS.clear(); assert codes == [200, 200, 200, 429, 429]
def test_unknown_route_is_json():
    r = c.get("/nope"); assert r.status_code == 404 and r.json()["error"]["code"] == "http_error"
def test_internal_errors_dont_leak(monkeypatch):
    def boom(*a): raise RuntimeError("secret internal detail")
    monkeypatch.setattr(main, "classify", boom)
    r = c.post("/predict", files={"file": ("a.png", png(XT[0]), "image/png")}); assert r.status_code == 500 and "secret" not in r.text
def test_model_missing_gives_503(monkeypatch):
    monkeypatch.setitem(main.STATE, "model", None); monkeypatch.setitem(main.STATE, "load_error", "no model")
    assert c.post("/predict", files={"file": ("a.png", png(XT[0]), "image/png")}).status_code == 503 and c.get("/health").json()["status"] == "degraded"
