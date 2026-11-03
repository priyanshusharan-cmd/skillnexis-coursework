import io

import pytest

from library import cli
from library.books import AudioBook, BookFactory, EBook, PrintedBook
from library.db import Database
from library.events import AuditLog, EventBus, LowStockAlert, MemberNotifier
from library.service import LibraryService, NotFound

CLEAN_CODE = "9780132350884"
PRAGMATIC = "9780135957059"
SICP = "9780262510875"


@pytest.fixture
def db():
    Database.close()
    d = Database(":memory:")
    yield d
    Database.close()


@pytest.fixture
def lib(db):
    bus = EventBus()
    notifier, audit, low = MemberNotifier(), AuditLog(clock=lambda: __import__("datetime").datetime(2026, 1, 1)), LowStockAlert()
    for e in ("book_borrowed", "book_returned", "book_available"):
        bus.subscribe(e, notifier)
    for e in ("book_added", "book_deleted", "book_borrowed", "book_returned", "waitlisted", "book_available"):
        bus.subscribe(e, audit)
    bus.subscribe("book_borrowed", low)
    svc = LibraryService(db, bus)
    svc.notifier, svc.audit, svc.low = notifier, audit, low
    return svc


# ---------------------------------------------------------------- Singleton
def test_database_is_a_singleton(db):
    assert Database(":memory:") is db
    with pytest.raises(RuntimeError):
        Database("other.db")


# ---------------------------------------------------------------- Factory
def test_factory_builds_each_kind_from_extra():
    assert isinstance(BookFactory.create("printed", title="A", author="B", isbn=CLEAN_CODE, extra="464"), PrintedBook)
    e = BookFactory.create("ebook", title="A", author="B", isbn=CLEAN_CODE, extra="3.5")
    assert isinstance(e, EBook) and e.size_mb == 3.5
    a = BookFactory.create("audiobook", title="A", author="B", isbn="978-0-13-235088-4", extra="")
    assert isinstance(a, AudioBook) and a.minutes == 0 and a.isbn == CLEAN_CODE
    assert BookFactory.kinds() == ["printed", "ebook", "audiobook"]


@pytest.mark.parametrize("fields,msg", [
    ({"kind": "scroll"}, "unknown book kind"),
    ({"title": "  "}, "title and author"),
    ({"isbn": "12345"}, "13 digits"),
    ({"isbn": "9780132350885"}, "check digit"),
    ({"copies": -1}, "copies"),
    ({"copies": 2, "available": 3}, "available"),
])
def test_factory_validation(fields, msg):
    base = {"kind": "printed", "title": "T", "author": "A", "isbn": CLEAN_CODE}
    base.update(fields)
    kind = base.pop("kind")
    with pytest.raises(ValueError, match=msg):
        BookFactory.create(kind, **base)


def test_ebook_needs_a_licence():
    with pytest.raises(ValueError, match="licence"):
        BookFactory.create("ebook", title="T", author="A", isbn=CLEAN_CODE, copies=0)


# ---------------------------------------------------------------- CRUD
def test_book_crud(lib):
    b = lib.add_book("printed", title="Clean Code", author="Robert C. Martin", isbn=CLEAN_CODE, copies=2, extra="464")
    lib.add_book("ebook", title="The Pragmatic Programmer", author="Hunt & Thomas", isbn=PRAGMATIC, extra="12.5")
    assert lib.get_book(b.id).describe() == "#1 Clean Code by Robert C. Martin [printed] 2/2 available"
    assert [x.title for x in lib.list_books()] == ["Clean Code", "The Pragmatic Programmer"]
    assert [x.title for x in lib.list_books("hunt")] == ["The Pragmatic Programmer"]
    assert lib.update_book(b.id, copies=5, title="Clean Code (2nd)").describe().endswith("5/5 available")
    assert lib.get_book(b.id).pages == 464
    lib.delete_book(b.id)
    with pytest.raises(NotFound):
        lib.get_book(b.id)
    assert [e.split(" ", 1)[1] for e in lib.audit.entries[:3]] == [
        "book_added book_id=1 title=Clean Code", "book_added book_id=2 title=The Pragmatic Programmer", "book_deleted book_id=1 title=Clean Code (2nd)"]


def test_duplicate_isbn_and_bad_updates(lib):
    b = lib.add_book("printed", title="SICP", author="Abelson", isbn=SICP)
    with pytest.raises(ValueError, match="already exists"):
        lib.add_book("printed", title="Copy", author="X", isbn=SICP)
    with pytest.raises(ValueError, match="can only update"):
        lib.update_book(b.id, isbn=CLEAN_CODE)
    with pytest.raises(ValueError, match="title and author"):
        lib.update_book(b.id, title="")


# ---------------------------------------------------------------- lending + Observer
def test_borrow_return_waitlist_and_notifications(lib):
    book = lib.add_book("printed", title="SICP", author="Abelson", isbn=SICP, copies=1)
    priya = lib.add_member("Priya Rao", "Priya@Example.com")
    arjun = lib.add_member("Arjun", "arjun@example.com")

    loan = lib.borrow(book.id, priya)
    assert lib.get_book(book.id).available == 0
    assert lib.low.alerts == ["Last copy of 'SICP' is out"]
    with pytest.raises(ValueError, match="already has"):
        lib.borrow(book.id, priya)
    assert lib.borrow(book.id, arjun) is None  # no copy free: waitlisted
    with pytest.raises(ValueError, match="on loan"):
        lib.update_book(book.id, copies=0)
    with pytest.raises(ValueError, match="on loan"):
        lib.delete_book(book.id)
    assert [r["title"] for r in lib.loans(priya)] == ["SICP"]

    lib.return_book(loan)
    assert lib.get_book(book.id).available == 1 and lib.loans(priya) == []
    assert lib.notifier.outbox == [
        ("priya@example.com", "Hi Priya Rao, you borrowed 'SICP'. Enjoy!"),
        ("priya@example.com", "Thanks Priya Rao, 'SICP' is returned."),
        ("arjun@example.com", "Good news Arjun: 'SICP' is available. It is held for you."),
    ]
    assert lib.borrow(book.id, arjun)  # waitlisted member can now borrow; leaves the waitlist
    assert lib.db.query("SELECT COUNT(*) AS n FROM waitlist")[0]["n"] == 0
    with pytest.raises(NotFound):
        lib.return_book(loan)  # already returned


def test_member_validation_and_unknown_ids(lib):
    lib.add_member("A", "a@b.co")
    with pytest.raises(ValueError, match="already a member"):
        lib.add_member("A2", "A@B.co")
    with pytest.raises(ValueError, match="valid email"):
        lib.add_member("B", "not-an-email")
    with pytest.raises(NotFound):
        lib.borrow(99, 1)
    book = lib.add_book("printed", title="T", author="A", isbn=SICP)
    with pytest.raises(NotFound):
        lib.borrow(book.id, 99)


def test_unsubscribe_stops_notifications(lib):
    lib.bus.unsubscribe("book_borrowed", lib.notifier)
    book = lib.add_book("printed", title="T", author="A", isbn=SICP)
    lib.borrow(book.id, lib.add_member("A", "a@b.co"))
    assert lib.notifier.outbox == []


# ---------------------------------------------------------------- CLI
def run(args, tmp_path, monkeypatch):
    monkeypatch.setenv("LIBRARY_DB", str(tmp_path / "lib.db"))
    out = io.StringIO()
    code = cli.main(args, out=out)
    return code, out.getvalue().strip()


def test_cli_end_to_end(tmp_path, monkeypatch):
    Database.close()
    assert run(["add", "printed", "Clean Code", "Robert C. Martin", CLEAN_CODE, "--copies", "1", "--extra", "464"], tmp_path, monkeypatch) == (0, "Added #1 Clean Code by Robert C. Martin [printed] 1/1 available")
    assert run(["list"], tmp_path, monkeypatch)[1] == "#1 Clean Code by Robert C. Martin [printed] 1/1 available"
    assert run(["list", "--search", "zzz"], tmp_path, monkeypatch)[1] == "No books found"
    assert run(["show", "1"], tmp_path, monkeypatch)[0] == 0
    assert run(["update", "1", "--copies", "2"], tmp_path, monkeypatch)[1].endswith("2/2 available")
    assert run(["member", "Priya", "priya@example.com"], tmp_path, monkeypatch)[1] == "Member 1 registered"
    code, text = run(["borrow", "1", "1"], tmp_path, monkeypatch)
    assert code == 0 and text.splitlines() == ["Loan 1 created", "  -> notify priya@example.com: Hi Priya, you borrowed 'Clean Code'. Enjoy!"]
    assert run(["loans", "1"], tmp_path, monkeypatch)[1] == "loan 1: Clean Code"
    assert run(["return", "1"], tmp_path, monkeypatch)[1].startswith("Loan 1 returned")
    assert run(["loans", "1"], tmp_path, monkeypatch)[1] == "No open loans"
    assert run(["delete", "1"], tmp_path, monkeypatch)[1] == "Deleted book 1"
    assert run(["show", "1"], tmp_path, monkeypatch) == (1, "Error: no book with id 1")


def test_cli_waitlist_and_low_stock(tmp_path, monkeypatch):
    Database.close()
    run(["add", "ebook", "SICP", "Abelson", SICP], tmp_path, monkeypatch)
    run(["member", "A", "a@b.co"], tmp_path, monkeypatch)
    run(["member", "B", "b@b.co"], tmp_path, monkeypatch)
    assert "!! Last copy of 'SICP' is out" in run(["borrow", "1", "1"], tmp_path, monkeypatch)[1]
    assert run(["borrow", "1", "2"], tmp_path, monkeypatch)[1] == "No copies free: added to the waitlist"
    assert "Good news B: 'SICP' is available" in run(["return", "1"], tmp_path, monkeypatch)[1]
