"""Command-line admin:  python -m app.admin create-user NAME [--role admin] [--limit 200000]   (prints the API key once)
                      python -m app.admin users"""
import argparse
from . import store
p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="cmd", required=True)
c = sub.add_parser("create-user"); c.add_argument("name"); c.add_argument("--role", default="user", choices=["user", "admin"]); c.add_argument("--limit", type=int, default=200_000)
sub.add_parser("users"); a = p.parse_args(); store.init()
if a.cmd == "create-user": print(store.create_user(a.name, a.role, a.limit))
else:
    with store.conn() as cx:
        for r in cx.execute("SELECT name, role, daily_token_limit, created FROM users"): print(dict(r))
