"""Regression test for DEF-1 (found in week 4): links in the nav bar and the Checkout link were
20 px tall, under the 24 px minimum target size (WCAG 2.2, 2.5.8). Every link and button must
now be at least 24 x 24 px."""
from pages import InventoryPage, LoginPage

SMALL = """return [...document.querySelectorAll('a,button')]
  .map(e => [e.textContent.trim(), e.getBoundingClientRect()])
  .filter(([, r]) => r.height > 0 && (r.height < 24 || r.width < 24))
  .map(([t, r]) => `${t} ${Math.round(r.width)}x${Math.round(r.height)}`)"""


def test_def1_tap_targets_are_at_least_24px(driver, base_url):
    LoginPage(driver, base_url).open()
    assert driver.execute_script(SMALL) == [], "login page"
    LoginPage(driver, base_url).login("standard_user", "demo-pass-123")
    inv = InventoryPage(driver, base_url)
    inv.add_to_cart("Notebook Set")
    for path in ["/inventory", "/cart", "/checkout"]:
        driver.get(base_url + path)
        assert driver.execute_script(SMALL) == [], path
