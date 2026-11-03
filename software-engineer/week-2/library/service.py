"""Library service: book CRUD (Factory), lending and waitlists (Observer), storage (Singleton DB)."""
import re
import sqlite3

from .books import BookFactory
from .db import Database
from .events import EventBus

EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class NotFound(LookupError):
    pass


class LibraryService:
    def __init__(self, db=None, bus=None):
        self.db = db or Database()
        self.bus = bus or EventBus()

    # ---------------------------------------------------------------- books (CRUD)
    def add_book(self, kind, **fields):
        book = BookFactory.create(kind, **fields)
        try:
            cur = self.db.execute(
                "INSERT INTO books (kind, title, author, isbn, extra, copies, available) VALUES (?,?,?,?,?,?,?)",
                (book.kind, book.title, book.author, book.isbn, book.extra, book.copies, book.available))
        except sqlite3.IntegrityError:
            raise ValueError(f"a book with ISBN {book.isbn} already exists") from None
        book.id = cur.lastrowid
        self.bus.publish("book_added", book_id=book.id, title=book.title)
        return book

    def get_book(self, book_id):
        rows = self.db.query("SELECT * FROM books WHERE id = ?", (book_id,))
        if not rows:
            raise NotFound(f"no book with id {book_id}")
        return BookFactory.from_row(rows[0])

    def list_books(self, search=""):
        like = f"%{search}%"
        rows = self.db.query("SELECT * FROM books WHERE title LIKE ? OR author LIKE ? ORDER BY title", (like, like))
        return [BookFactory.from_row(r) for r in rows]

    def update_book(self, book_id, **changes):
        book = self.get_book(book_id)
        allowed = {"title", "author", "copies"}
        if set(changes) - allowed:
            raise ValueError(f"can only update {', '.join(sorted(allowed))}")
        on_loan = book.copies - book.available
        if "copies" in changes and changes["copies"] < on_loan:
            raise ValueError(f"{on_loan} copies are on loan; copies cannot go below that")
        fields = {"title": book.title, "author": book.author, "isbn": book.isbn, "copies": book.copies, "extra": book.extra, **changes}
        updated = BookFactory.create(book.kind, id=book_id, available=fields["copies"] - on_loan, **fields)  # re-validates
        self.db.execute("UPDATE books SET title=?, author=?, copies=?, available=? WHERE id=?",
                        (updated.title, updated.author, updated.copies, updated.available, book_id))
        self.bus.publish("book_updated", book_id=book_id, title=updated.title)
        return updated

    def delete_book(self, book_id):
        book = self.get_book(book_id)
        if book.available != book.copies:
            raise ValueError("cannot delete a book while copies are on loan")
        self.db.execute("DELETE FROM loans WHERE book_id = ?", (book_id,))
        self.db.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self.bus.publish("book_deleted", book_id=book_id, title=book.title)

    # ---------------------------------------------------------------- members
    def add_member(self, name, email):
        if not name.strip() or not EMAIL.match(email):
            raise ValueError("a name and a valid email are required")
        try:
            cur = self.db.execute("INSERT INTO members (name, email) VALUES (?, ?)", (name.strip(), email.lower()))
        except sqlite3.IntegrityError:
            raise ValueError(f"{email} is already a member") from None
        return cur.lastrowid

    def _member(self, member_id):
        rows = self.db.query("SELECT * FROM members WHERE id = ?", (member_id,))
        if not rows:
            raise NotFound(f"no member with id {member_id}")
        return rows[0]

    # ---------------------------------------------------------------- lending
    def borrow(self, book_id, member_id):
        book, member = self.get_book(book_id), self._member(member_id)
        if self.db.query("SELECT 1 FROM loans WHERE book_id=? AND member_id=? AND returned=0", (book_id, member_id)):
            raise ValueError("this member already has this book")
        if book.available == 0:
            self.db.execute("INSERT OR IGNORE INTO waitlist VALUES (?, ?)", (book_id, member_id))
            self.bus.publish("waitlisted", book_id=book_id, member_id=member_id, title=book.title)
            return None
        cur = self.db.execute("INSERT INTO loans (book_id, member_id) VALUES (?, ?)", (book_id, member_id))
        self.db.execute("UPDATE books SET available = available - 1 WHERE id = ?", (book_id,))
        self.db.execute("DELETE FROM waitlist WHERE book_id=? AND member_id=?", (book_id, member_id))
        self.bus.publish("book_borrowed", book_id=book_id, member_id=member_id, title=book.title,
                         name=member["name"], email=member["email"], available=book.available - 1)
        return cur.lastrowid

    def return_book(self, loan_id):
        rows = self.db.query("SELECT * FROM loans WHERE id = ? AND returned = 0", (loan_id,))
        if not rows:
            raise NotFound(f"no open loan with id {loan_id}")
        loan = rows[0]
        book, member = self.get_book(loan["book_id"]), self._member(loan["member_id"])
        self.db.execute("UPDATE loans SET returned = 1 WHERE id = ?", (loan_id,))
        self.db.execute("UPDATE books SET available = available + 1 WHERE id = ?", (book.id,))
        self.bus.publish("book_returned", book_id=book.id, member_id=member["id"], title=book.title, name=member["name"], email=member["email"])
        waiting = self.db.query(
            "SELECT m.* FROM waitlist w JOIN members m ON m.id = w.member_id WHERE w.book_id = ? ORDER BY w.rowid LIMIT 1", (book.id,))
        if waiting:
            w = waiting[0]
            self.bus.publish("book_available", book_id=book.id, member_id=w["id"], title=book.title, name=w["name"], email=w["email"])
        return book.id

    def loans(self, member_id):
        return self.db.query(
            "SELECT l.id, b.title FROM loans l JOIN books b ON b.id = l.book_id WHERE l.member_id = ? AND l.returned = 0 ORDER BY l.id", (member_id,))
