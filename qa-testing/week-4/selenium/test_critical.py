"""Critical scenarios C11–C15. C01–C10 are the week 3 scenarios (../../week-3/selenium/test_scenarios.py);
CI runs both files together as the 15-scenario critical pack."""
import pytest
from selenium.webdriver.common.by import By

from pages import CartPage, InventoryPage, LoginPage


@pytest.fixture
def shop(driver, base_url):
    LoginPage(driver, base_url).open().login("standard_user", "demo-pass-123")
    return InventoryPage(driver, base_url)


def test_c11_checkout_page_requires_login(driver, base_url):
    driver.get(base_url + "/checkout")
    page = LoginPage(driver, base_url)
    assert page.heading() == "Log in"
    assert page.error() == "Please log in first"


def test_c12_quantity_above_ten_is_rejected(shop):
    shop.add_to_cart("Notebook Set")
    cart = shop.go_to_cart()
    cart.set_qty("Notebook Set", 11)
    assert cart.find(*cart.ERROR).text == "Quantity must be a whole number from 1 to 10"
    assert cart.items() == {"Notebook Set": 1}  # unchanged


def test_c13_quantity_above_stock_is_rejected(shop):
    shop.add_to_cart("Desk Lamp")  # 5 in stock
    cart = shop.go_to_cart()
    cart.set_qty("Desk Lamp", 6)
    assert cart.find(*cart.ERROR).text == "Only 5 in stock"
    assert cart.items() == {"Desk Lamp": 1}


def test_c14_search_text_is_escaped_not_rendered(shop, driver):
    shop.search('<b id="injected">bold</b>')
    assert driver.find_elements(By.ID, "injected") == []  # no element was created from user input
    assert '<b id="injected">bold</b>' in shop.find(*shop.NO_RESULTS).text


def test_c15_cart_survives_navigation_and_empty_cart_cannot_checkout(shop, driver, base_url):
    shop.add_to_cart("Steel Water Bottle")
    shop.search("mouse")
    shop.add_to_cart("Wireless Mouse")
    driver.get(base_url + "/inventory")
    cart = shop.go_to_cart()
    assert cart.items() == {"Steel Water Bottle": 1, "Wireless Mouse": 1}
    cart.remove("Steel Water Bottle")
    cart.remove("Wireless Mouse")
    assert driver.find_elements(By.ID, "checkout") == []  # no Checkout link on an empty cart
    driver.get(base_url + "/checkout")
    driver.find_element(By.ID, "first-name").send_keys("Priya")
    driver.find_element(By.ID, "last-name").send_keys("Rao")
    driver.find_element(By.ID, "email").send_keys("priya@example.com")
    driver.find_element(By.ID, "postal-code").send_keys("560019")
    driver.find_element(By.ID, "place-order").click()
    assert [e.text for e in driver.find_elements(By.CSS_SELECTOR, "#checkout-errors li")] == ["Cart is empty"]
