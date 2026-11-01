"""Python Week 3: OOP, exception handling and the math, random and datetime modules."""
import math
import random
from datetime import datetime


class InsufficientFunds(Exception):
    pass


class BankAccount:
    def __init__(self, owner, balance=0.0):
        if balance < 0:
            raise ValueError("opening balance cannot be negative")
        self.owner = owner
        self.balance = float(balance)

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("deposit must be positive")
        self.balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("withdrawal must be positive")
        if amount > self.balance:
            raise InsufficientFunds(f"balance {self.balance:.2f} is less than {amount:.2f}")
        self.balance -= amount

    def display_balance(self):
        print(f"{self.owner}: balance {self.balance:.2f}")


class Book:
    def __init__(self, book_id, title):
        self.book_id = book_id
        self.title = title
        self.issued_to = None
        self.issued_at = None


class Library:
    def __init__(self):
        self.books = {}

    def add_book(self, book):
        if book.book_id in self.books:
            raise ValueError(f"book id {book.book_id} already exists")
        self.books[book.book_id] = book

    def remove_book(self, book_id):
        book = self.books.get(book_id)
        if book is None:
            raise KeyError(f"no book with id {book_id}")
        if book.issued_to:
            raise ValueError("cannot remove an issued book")
        del self.books[book_id]

    def issue_book(self, book_id, member):
        book = self.books.get(book_id)
        if book is None:
            raise KeyError(f"no book with id {book_id}")
        if book.issued_to:
            raise ValueError(f"'{book.title}' is already issued to {book.issued_to}")
        book.issued_to = member
        book.issued_at = datetime.now()

    def return_book(self, book_id):
        book = self.books.get(book_id)
        if book is None or not book.issued_to:
            raise ValueError("that book is not currently issued")
        book.issued_to = None
        book.issued_at = None

    def show(self):
        for b in self.books.values():
            status = f"issued to {b.issued_to} on {b.issued_at:%Y-%m-%d}" if b.issued_to else "available"
            print(f"  #{b.book_id} {b.title}: {status}")


class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        try:
            return a / b
        except ZeroDivisionError:
            raise ValueError("cannot divide by zero") from None

    def sqrt(self, a):
        if a < 0:
            raise ValueError("square root of a negative number")
        return math.sqrt(a)


class Product:
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

    @property
    def amount(self):
        return self.price * self.quantity


class Bill:
    def __init__(self, tax_rate=0.18):
        self.items = []
        self.tax_rate = tax_rate

    def add(self, product):
        self.items.append(product)

    def subtotal(self):
        return sum(p.amount for p in self.items)

    def tax(self):
        return round(self.subtotal() * self.tax_rate, 2)

    def total(self):
        return self.subtotal() + self.tax()

    def display(self):
        print(f"{'Item':<12}{'Price':>10}{'Qty':>5}{'Amount':>12}")
        print("-" * 39)
        for p in self.items:
            print(f"{p.name:<12}{p.price:>10.2f}{p.quantity:>5}{p.amount:>12.2f}")
        print("-" * 39)
        print(f"{'Subtotal':<27}{self.subtotal():>12.2f}")
        print(f"{'GST ' + format(self.tax_rate * 100, '.0f') + '%':<27}{self.tax():>12.2f}")
        print(f"{'Total':<27}{self.total():>12.2f}")


def main():
    print("1. Bank account")
    acc = BankAccount("Asha", 1000)
    acc.deposit(500)
    acc.withdraw(300)
    acc.display_balance()
    for bad in (lambda: acc.withdraw(5000), lambda: acc.deposit(-1)):
        try:
            bad()
        except (InsufficientFunds, ValueError) as err:
            print("  rejected:", err)

    print("2. Library management")
    lib = Library()
    lib.add_book(Book(1, "Python Crash Course"))
    lib.add_book(Book(2, "Fluent Python"))
    lib.issue_book(1, "Ravi")
    try:
        lib.issue_book(1, "Meera")
    except ValueError as err:
        print("  rejected:", err)
    lib.show()
    lib.return_book(1)
    lib.remove_book(2)
    lib.show()

    print("3. Calculator with exception handling")
    calc = Calculator()
    print("  7 + 3 =", calc.add(7, 3), "| 7 / 2 =", calc.divide(7, 2), "| sqrt(16) =", calc.sqrt(16))
    for fn, args in ((calc.divide, (1, 0)), (calc.sqrt, (-4,))):
        try:
            fn(*args)
        except ValueError as err:
            print("  rejected:", err)

    print("Billing system (seeded random quantities so the output is repeatable)")
    random.seed(7)
    bill = Bill()
    for name, price in (("Notebook", 45.5), ("Pen", 10.0), ("Backpack", 899.0)):
        bill.add(Product(name, price, random.randint(1, 5)))
    print(f"Date: {datetime.now():%d-%m-%Y}")
    bill.display()


if __name__ == "__main__":
    main()
