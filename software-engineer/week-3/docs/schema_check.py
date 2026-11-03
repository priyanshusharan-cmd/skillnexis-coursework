"""Load social-media-schema.sql into SQLite (after small dialect changes), insert sample data,
check that the constraints reject bad rows, and run the queries from social-media-schema.md.

usage: python docs/schema_check.py
"""
import re
import sqlite3
from pathlib import Path

sql = Path(__file__).with_name("social-media-schema.sql").read_text()
# PostgreSQL -> SQLite
sql = re.sub(r"BIGSERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT", sql)
sql = sql.replace("TIMESTAMPTZ", "TEXT").replace("now()", "CURRENT_TIMESTAMP")

db = sqlite3.connect(":memory:")
db.execute("PRAGMA foreign_keys = ON")
db.executescript(sql)

q = db.execute
for name in ("priya", "arjun", "meera"):
    q("INSERT INTO users (username, email, password_hash, display_name) VALUES (?, ?, 'x', ?)", (name, f"{name}@example.com", name.title()))
q("INSERT INTO follows (follower_id, followee_id) VALUES (1, 2), (1, 3), (2, 3)")
for author, body in [(2, "Hello #python"), (3, "System design notes #python #sysdesign"), (3, "Lunch"), (1, "My first post")]:
    q("INSERT INTO posts (author_id, body) VALUES (?, ?)", (author, body))
q("INSERT INTO hashtags (tag) VALUES ('python'), ('sysdesign')")
q("INSERT INTO post_hashtags VALUES (1, 1), (2, 1), (2, 2)")
q("INSERT INTO post_likes (post_id, user_id) VALUES (2, 1), (2, 2), (1, 1)")
q("INSERT INTO comments (post_id, author_id, body) VALUES (2, 1, 'Great notes')")
q("INSERT INTO comments (post_id, author_id, parent_id, body) VALUES (2, 3, 1, 'Thanks!')")

checks = {
    "self-follow rejected": "INSERT INTO follows (follower_id, followee_id) VALUES (1, 1)",
    "double like rejected": "INSERT INTO post_likes (post_id, user_id) VALUES (2, 1)",
    "duplicate email rejected": "INSERT INTO users (username, email, password_hash, display_name) VALUES ('x', 'priya@example.com', 'x', 'X')",
    "like on missing post rejected": "INSERT INTO post_likes (post_id, user_id) VALUES (99, 1)",
    "bad notification type rejected": "INSERT INTO notifications (user_id, actor_id, type) VALUES (1, 2, 'poke')",
}
for label, stmt in checks.items():
    try:
        q(stmt)
        print("FAIL", label)
    except sqlite3.IntegrityError:
        print("ok  ", label)

print("\nHome feed for priya (people she follows, newest first):")
for row in q("""SELECT u.username, p.body, (SELECT COUNT(*) FROM post_likes l WHERE l.post_id = p.id) AS likes
                FROM posts p JOIN follows f ON f.followee_id = p.author_id JOIN users u ON u.id = p.author_id
                WHERE f.follower_id = 1 ORDER BY p.created_at DESC, p.id DESC LIMIT 20"""):
    print("  ", row)

print("\nPosts tagged #python:")
for row in q("""SELECT p.id, p.body FROM posts p JOIN post_hashtags ph ON ph.post_id = p.id
                JOIN hashtags h ON h.id = ph.hashtag_id WHERE h.tag = 'python' ORDER BY p.id"""):
    print("  ", row)

print("\nFollower counts:")
for row in q("""SELECT u.username, COUNT(f.follower_id) FROM users u LEFT JOIN follows f ON f.followee_id = u.id
                GROUP BY u.id ORDER BY 2 DESC, u.username"""):
    print("  ", row)

q("DELETE FROM users WHERE id = 3")
left = q("SELECT COUNT(*) FROM posts WHERE author_id = 3").fetchone()[0] + q("SELECT COUNT(*) FROM post_hashtags WHERE post_id = 2").fetchone()[0]
print("\nDeleting meera cascades to her posts, tags links and likes:", "ok" if left == 0 else "FAIL")
