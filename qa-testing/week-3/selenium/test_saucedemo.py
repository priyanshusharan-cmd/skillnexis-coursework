"""Login automation on the public practice site saucedemo.com.

Skipped unless SAUCEDEMO=1, since it needs internet access. The credentials are the
public practice accounts printed on the site's own login page.
"""
import os

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

pytestmark = pytest.mark.skipif(os.environ.get("SAUCEDEMO") != "1", reason="set SAUCEDEMO=1 to run against saucedemo.com")
URL = "https://www.saucedemo.com/"


def _login(driver, user):
    driver.get(URL)
    driver.find_element(By.ID, "user-name").send_keys(user)
    driver.find_element(By.ID, "password").send_keys("secret_sauce")
    driver.find_element(By.ID, "login-button").click()


def test_saucedemo_standard_user_reaches_inventory(driver):
    _login(driver, "standard_user")
    title = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".title")))
    assert title.text == "Products"


def test_saucedemo_locked_user_sees_error(driver):
    _login(driver, "locked_out_user")
    err = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-test='error']")))
    assert "locked out" in err.text
