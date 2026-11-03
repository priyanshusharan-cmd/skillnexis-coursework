"""Page objects for the Demo Shop. Locators deliberately mix the three strategies
covered this week: element IDs, CSS selectors and XPath."""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 5)

    def find(self, by, value):
        return self.wait.until(EC.visibility_of_element_located((by, value)))

    def heading(self):
        return self.find(By.TAG_NAME, "h1").text

    def cart_count(self):
        return int(self.find(By.ID, "cart-count").text)


class LoginPage(BasePage):
    USERNAME = (By.ID, "username")
    PASSWORD = (By.ID, "password")
    SUBMIT = (By.CSS_SELECTOR, "#login-form button[type='submit']")
    ERROR = (By.XPATH, "//p[@role='alert' and @id='login-error']")

    def open(self):
        self.driver.get(self.base_url + "/")
        return self

    def login(self, username, password):
        user = self.find(*self.USERNAME)
        user.clear()
        user.send_keys(username)
        pw = self.find(*self.PASSWORD)
        pw.clear()
        pw.send_keys(password)
        self.find(*self.SUBMIT).click()

    def error(self):
        return self.find(*self.ERROR).text


class InventoryPage(BasePage):
    SEARCH = (By.ID, "search")
    SEARCH_BUTTON = (By.ID, "search-button")
    NAMES = (By.CSS_SELECTOR, ".item .item-name")
    COUNT = (By.ID, "result-count")
    NO_RESULTS = (By.ID, "no-results")
    FLASH = (By.ID, "flash")

    def search(self, text):
        box = self.find(*self.SEARCH)
        box.clear()
        box.send_keys(text)
        self.find(*self.SEARCH_BUTTON).click()

    def product_names(self):
        return [e.text for e in self.driver.find_elements(*self.NAMES)]

    def add_to_cart(self, product_name):
        # XPath: the "Add to cart" button inside the row whose name matches.
        xp = f"//div[contains(@class,'item')][span[@class='item-name' and normalize-space()='{product_name}']]//button[contains(@class,'add-to-cart')]"
        self.find(By.XPATH, xp).click()

    def go_to_cart(self):
        self.find(By.ID, "nav-cart").click()
        return CartPage(self.driver, self.base_url)

    def logout(self):
        self.find(By.ID, "logout").click()


class CartPage(BasePage):
    ROWS = (By.CSS_SELECTOR, ".cart-item")
    TOTAL = (By.ID, "cart-total")
    EMPTY = (By.ID, "empty-cart")
    ERROR = (By.ID, "cart-error")

    def items(self):
        rows = self.driver.find_elements(*self.ROWS)
        return {r.find_element(By.CSS_SELECTOR, ".item-name").text: int(r.find_element(By.CSS_SELECTOR, "input.qty").get_attribute("value")) for r in rows}

    def set_qty(self, product_name, qty):
        row = self.find(By.XPATH, f"//div[contains(@class,'cart-item')][span[normalize-space()='{product_name}']]")
        box = row.find_element(By.CSS_SELECTOR, "input.qty")
        box.clear()
        box.send_keys(str(qty))
        row.find_element(By.CSS_SELECTOR, "button.update").click()

    def remove(self, product_name):
        self.find(By.XPATH, f"//div[contains(@class,'cart-item')][span[normalize-space()='{product_name}']]//button[contains(@class,'remove')]").click()

    def total(self):
        return float(self.find(*self.TOTAL).text.replace("₹", ""))

    def checkout(self):
        self.find(By.ID, "checkout").click()
        return CheckoutPage(self.driver, self.base_url)


class CheckoutPage(BasePage):
    FIELDS = {"first": (By.ID, "first-name"), "last": (By.ID, "last-name"), "email": (By.ID, "email"), "pin": (By.ID, "postal-code")}
    SUBMIT = (By.ID, "place-order")
    ERRORS = (By.CSS_SELECTOR, "#checkout-errors li")
    CONFIRMATION = (By.ID, "order-confirmation")

    def fill(self, first="", last="", email="", pin=""):
        for key, value in {"first": first, "last": last, "email": email, "pin": pin}.items():
            el = self.find(*self.FIELDS[key])
            el.clear()
            if value:
                el.send_keys(value)
        self.find(*self.SUBMIT).click()

    def errors(self):
        return [e.text for e in self.driver.find_elements(*self.ERRORS)]

    def confirmation(self):
        return self.find(*self.CONFIRMATION).text
