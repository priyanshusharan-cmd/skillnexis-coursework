"""Mini project: 10 automated end-to-end scenarios (login, search, cart, checkout)."""
import pytest

from pages import CheckoutPage, InventoryPage, LoginPage

USER, PASSWORD = "standard_user", "demo-pass-123"


@pytest.fixture
def shop(driver, base_url):
    """Logged-in inventory page."""
    LoginPage(driver, base_url).open().login(USER, PASSWORD)
    inv = InventoryPage(driver, base_url)
    assert inv.heading() == "Products"
    return inv


def test_s01_login_with_valid_credentials(driver, base_url):
    LoginPage(driver, base_url).open().login(USER, PASSWORD)
    inv = InventoryPage(driver, base_url)
    assert inv.heading() == "Products"
    assert driver.current_url.endswith("/inventory")
    assert len(inv.product_names()) == 5


def test_s02_login_with_wrong_password_shows_error(driver, base_url):
    page = LoginPage(driver, base_url).open()
    page.login(USER, "wrong-password")
    assert page.error() == "Username and password do not match"
    assert page.heading() == "Log in"


def test_s03_locked_out_user_cannot_log_in(driver, base_url):
    page = LoginPage(driver, base_url).open()
    page.login("locked_user", PASSWORD)
    assert page.error() == "This user has been locked out"


def test_s04_logout_ends_session(shop, driver, base_url):
    shop.logout()
    assert LoginPage(driver, base_url).heading() == "Log in"
    driver.get(base_url + "/inventory")  # protected page after logout
    assert LoginPage(driver, base_url).error() == "Please log in first"


def test_s05_search_finds_matching_products(shop):
    shop.search("lamp")
    assert shop.product_names() == ["Desk Lamp"]
    assert shop.find(*shop.COUNT).text == "1 product(s)"


def test_s06_search_with_no_match_shows_message(shop):
    shop.search("telescope")
    assert shop.product_names() == []
    assert 'No products match "telescope"' in shop.find(*shop.NO_RESULTS).text


def test_s07_add_two_products_to_cart(shop):
    shop.add_to_cart("Canvas Backpack")
    assert shop.find(*shop.FLASH).text == "Added to cart"
    shop.add_to_cart("Notebook Set")
    assert shop.cart_count() == 2
    cart = shop.go_to_cart()
    assert cart.items() == {"Canvas Backpack": 1, "Notebook Set": 1}
    assert cart.total() == pytest.approx(39.49)


def test_s08_update_quantity_recalculates_total(shop):
    shop.add_to_cart("Steel Water Bottle")
    cart = shop.go_to_cart()
    cart.set_qty("Steel Water Bottle", 3)
    assert cart.items() == {"Steel Water Bottle": 3}
    assert cart.total() == pytest.approx(46.50)
    assert cart.cart_count() == 3


def test_s09_remove_item_empties_cart(shop):
    shop.add_to_cart("Wireless Mouse")
    cart = shop.go_to_cart()
    cart.remove("Wireless Mouse")
    assert cart.find(*cart.EMPTY).text == "Your cart is empty."
    assert cart.cart_count() == 0


def test_s10_checkout_places_order(shop, driver, base_url):
    shop.add_to_cart("Notebook Set")
    checkout = shop.go_to_cart().checkout()
    checkout.fill(first="Priya", last="Rao", email="priya@example.com", pin="560019")
    assert checkout.heading() == "Order placed"
    assert "is confirmed" in checkout.confirmation()
    assert checkout.cart_count() == 0
