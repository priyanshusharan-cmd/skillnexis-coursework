"""Five automated form-validation scripts (login and checkout forms)."""
import pytest

from pages import InventoryPage, LoginPage


def test_v01_login_requires_username(driver, base_url):
    page = LoginPage(driver, base_url).open()
    page.login("", "anything")
    assert page.error() == "Username is required"


def test_v02_login_requires_password(driver, base_url):
    page = LoginPage(driver, base_url).open()
    page.login("standard_user", "")
    assert page.error() == "Password is required"


@pytest.fixture
def checkout(driver, base_url):
    LoginPage(driver, base_url).open().login("standard_user", "demo-pass-123")
    inv = InventoryPage(driver, base_url)
    inv.add_to_cart("Canvas Backpack")
    return inv.go_to_cart().checkout()


def test_v03_checkout_all_fields_required(checkout):
    checkout.fill()
    assert checkout.errors() == [
        "First name is required",
        "Last name is required",
        "Enter a valid email address",
        "PIN code must be 6 digits",
    ]


@pytest.mark.parametrize("email", ["priya", "priya@", "priya@example", "priya @example.com"])
def test_v04_checkout_rejects_invalid_email(checkout, email):
    checkout.fill(first="Priya", last="Rao", email=email, pin="560019")
    assert checkout.errors() == ["Enter a valid email address"]


@pytest.mark.parametrize("pin", ["56001", "5600199", "56O019", "      "])
def test_v05_checkout_rejects_bad_pin_code(checkout, pin):
    # boundary values: 5 and 7 digits, a letter O, and only spaces
    checkout.fill(first="Priya", last="Rao", email="priya@example.com", pin=pin)
    assert checkout.errors() == ["PIN code must be 6 digits"]
