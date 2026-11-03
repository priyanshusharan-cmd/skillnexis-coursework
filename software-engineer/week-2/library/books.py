"""Book types and the Factory that builds them from a kind name or a database row."""
import re
from dataclasses import dataclass, field

ISBN13 = re.compile(r"^97[89]\d{10}$")


def _check_isbn(isbn):
    digits = isbn.replace("-", "")
    if not ISBN13.match(digits):
        raise ValueError("ISBN must be 13 digits starting 978 or 979")
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits[:12]))
    if (10 - total % 10) % 10 != int(digits[12]):
        raise ValueError("ISBN check digit is wrong")
    return digits


@dataclass
class Book:
    title: str
    author: str
    isbn: str
    copies: int = 1
    available: int = field(default=None)
    id: int = None
    kind = "book"

    def __post_init__(self):
        self.title, self.author = self.title.strip(), self.author.strip()
        if not self.title or not self.author:
            raise ValueError("title and author are required")
        self.isbn = _check_isbn(self.isbn)
        if not isinstance(self.copies, int) or self.copies < 0:
            raise ValueError("copies must be a whole number >= 0")
        if self.available is None:
            self.available = self.copies
        if not 0 <= self.available <= self.copies:
            raise ValueError("available must be between 0 and copies")

    @property
    def extra(self):
        return ""

    def describe(self):
        return f"#{self.id} {self.title} by {self.author} [{self.kind}] {self.available}/{self.copies} available"


@dataclass
class PrintedBook(Book):
    pages: int = 0
    kind = "printed"

    @property
    def extra(self):
        return str(self.pages)


@dataclass
class EBook(Book):
    size_mb: float = 0.0
    kind = "ebook"

    def __post_init__(self):
        super().__post_init__()
        if self.copies < 1:  # copies are licences; an e-book with none cannot be lent
            raise ValueError("an e-book needs at least 1 licence")

    @property
    def extra(self):
        return str(self.size_mb)


@dataclass
class AudioBook(Book):
    minutes: int = 0
    kind = "audiobook"

    @property
    def extra(self):
        return str(self.minutes)


class BookFactory:
    _types = {"printed": (PrintedBook, "pages", int), "ebook": (EBook, "size_mb", float), "audiobook": (AudioBook, "minutes", int)}

    @classmethod
    def create(cls, kind, **fields):
        if kind not in cls._types:
            raise ValueError(f"unknown book kind {kind!r}; choose from {', '.join(cls._types)}")
        klass, extra_name, conv = cls._types[kind]
        if "extra" in fields:
            raw = fields.pop("extra")
            fields[extra_name] = conv(raw) if raw not in ("", None) else conv(0)
        return klass(**fields)

    @classmethod
    def from_row(cls, row):
        return cls.create(row["kind"], id=row["id"], title=row["title"], author=row["author"], isbn=row["isbn"],
                          copies=row["copies"], available=row["available"], extra=row["extra"])

    @classmethod
    def kinds(cls):
        return list(cls._types)
