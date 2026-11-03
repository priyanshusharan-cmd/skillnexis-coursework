"""Command-line interface.

  python -m library.cli add printed "Clean Code" "Robert C. Martin" 9780132350884 --copies 2 --extra 464
  python -m library.cli list [--search code]
  python -m library.cli show 1
  python -m library.cli update 1 --copies 3
  python -m library.cli delete 1
  python -m library.cli member "Priya Rao" priya@example.com
  python -m library.cli borrow 1 1
  python -m library.cli return 1
  python -m library.cli loans 1

Data lives in library.db (set LIBRARY_DB to use another file).
"""
import argparse
import os
import sys

from .db import Database
from .events import AuditLog, EventBus, LowStockAlert, MemberNotifier
from .service import LibraryService, NotFound


def build_parser():
    p = argparse.ArgumentParser(prog="library", description="Library management system")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="add a book")
    a.add_argument("kind", choices=["printed", "ebook", "audiobook"])
    a.add_argument("title")
    a.add_argument("author")
    a.add_argument("isbn")
    a.add_argument("--copies", type=int, default=1)
    a.add_argument("--extra", default="", help="pages / size in MB / minutes")
    ls = sub.add_parser("list", help="list books")
    ls.add_argument("--search", default="")
    for name in ("show", "delete"):
        sub.add_parser(name).add_argument("book_id", type=int)
    u = sub.add_parser("update")
    u.add_argument("book_id", type=int)
    u.add_argument("--title")
    u.add_argument("--author")
    u.add_argument("--copies", type=int)
    m = sub.add_parser("member", help="register a member")
    m.add_argument("name")
    m.add_argument("email")
    b = sub.add_parser("borrow")
    b.add_argument("book_id", type=int)
    b.add_argument("member_id", type=int)
    sub.add_parser("return").add_argument("loan_id", type=int)
    sub.add_parser("loans").add_argument("member_id", type=int)
    return p


def make_service(path):
    bus = EventBus()
    notifier, audit, low = MemberNotifier(), AuditLog(), LowStockAlert()
    for event in ("book_borrowed", "book_returned", "book_available"):
        bus.subscribe(event, notifier)
    for event in ("book_added", "book_updated", "book_deleted", "book_borrowed", "book_returned", "waitlisted", "book_available"):
        bus.subscribe(event, audit)
    bus.subscribe("book_borrowed", low)
    return LibraryService(Database(path), bus), notifier, audit, low


def main(argv=None, out=sys.stdout):
    args = build_parser().parse_args(argv)
    svc, notifier, _, low = make_service(os.environ.get("LIBRARY_DB", "library.db"))
    try:
        if args.cmd == "add":
            book = svc.add_book(args.kind, title=args.title, author=args.author, isbn=args.isbn, copies=args.copies, extra=args.extra)
            print(f"Added {book.describe()}", file=out)
        elif args.cmd == "list":
            books = svc.list_books(args.search)
            print("\n".join(b.describe() for b in books) or "No books found", file=out)
        elif args.cmd == "show":
            print(svc.get_book(args.book_id).describe(), file=out)
        elif args.cmd == "update":
            changes = {k: v for k, v in (("title", args.title), ("author", args.author), ("copies", args.copies)) if v is not None}
            print(f"Updated {svc.update_book(args.book_id, **changes).describe()}", file=out)
        elif args.cmd == "delete":
            svc.delete_book(args.book_id)
            print(f"Deleted book {args.book_id}", file=out)
        elif args.cmd == "member":
            print(f"Member {svc.add_member(args.name, args.email)} registered", file=out)
        elif args.cmd == "borrow":
            loan = svc.borrow(args.book_id, args.member_id)
            print(f"Loan {loan} created" if loan else "No copies free: added to the waitlist", file=out)
        elif args.cmd == "return":
            svc.return_book(args.loan_id)
            print(f"Loan {args.loan_id} returned", file=out)
        elif args.cmd == "loans":
            rows = svc.loans(args.member_id)
            print("\n".join(f"loan {r['id']}: {r['title']}" for r in rows) or "No open loans", file=out)
        for email, msg in notifier.outbox:
            print(f"  -> notify {email}: {msg}", file=out)
        for alert in low.alerts:
            print(f"  !! {alert}", file=out)
        return 0
    except (ValueError, NotFound) as e:
        print(f"Error: {e}", file=out)
        return 1
    finally:
        Database.close()


if __name__ == "__main__":
    raise SystemExit(main())
