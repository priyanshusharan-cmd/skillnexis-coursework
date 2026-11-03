"""Browser end-to-end tests: two real Firefox windows against a running uvicorn server.
Skipped unless E2E=1. Set FIREFOX_BIN / GECKODRIVER if they are not on PATH."""
import os
import socket
import subprocess
import sys
import time
import urllib.request

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.skipif(os.environ.get("E2E") != "1", reason="set E2E=1 to run browser tests")]


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    env = {**os.environ, "JWT_SECRET": "e2e-" + "s" * 40, "BLOG_DB": str(tmp_path_factory.mktemp("db") / "e2e.db"), "LOG_LEVEL": "WARNING", "LOGIN_LIMIT_PER_MIN": "100"}  # 3 users sign up from one IP
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "blogly.app:app", "--port", str(port)], env=env,
                            cwd=os.path.dirname(os.path.dirname(__file__)), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            urllib.request.urlopen(url + "/health", timeout=1)
            break
        except OSError:
            time.sleep(0.1)
    yield url
    proc.terminate()
    proc.wait(timeout=5)


def browser():
    from selenium import webdriver
    opts = webdriver.FirefoxOptions()
    opts.add_argument("-headless")
    if os.environ.get("FIREFOX_BIN"):
        opts.binary_location = os.environ["FIREFOX_BIN"]
    svc = webdriver.FirefoxService(executable_path=os.environ["GECKODRIVER"]) if os.environ.get("GECKODRIVER") else webdriver.FirefoxService()
    return webdriver.Firefox(options=opts, service=svc)


@pytest.fixture
def two_browsers():
    a, b = browser(), browser()
    yield a, b
    a.quit()
    b.quit()


def wait_for(fn, timeout=8):
    end = time.time() + timeout
    while time.time() < end:
        try:
            value = fn()
            if value:
                return value
        except Exception:
            pass
        time.sleep(0.1)
    raise AssertionError("condition not met in time")


def sign_up(d, url, name):
    from selenium.webdriver.common.by import By
    d.get(url)
    d.find_element(By.ID, "username").send_keys(name)
    d.find_element(By.ID, "password").send_keys("correct-horse-1")
    d.find_element(By.CSS_SELECTOR, "button[data-action=register]").click()
    wait_for(lambda: d.find_element(By.ID, "who").text == f"@{name}")


def test_post_appears_live_in_another_users_browser(server, two_browsers):
    from selenium.webdriver.common.by import By
    alice, bob = two_browsers
    sign_up(alice, server, "alice")
    sign_up(bob, server, "bob")
    wait_for(lambda: bob.find_element(By.ID, "live").text == "● live")

    alice.find_element(By.ID, "post-title").send_keys("Hello from Alice")
    alice.find_element(By.ID, "post-body").send_keys("<b>not bold</b> and a newline\nhere")
    alice.find_element(By.CSS_SELECTOR, "#post-form button").click()

    # Bob never reloads: the post must arrive over the WebSocket.
    card = wait_for(lambda: bob.find_element(By.CSS_SELECTOR, "#feed .post .title"))
    assert card.text == "Hello from Alice"
    body = bob.find_element(By.CSS_SELECTOR, "#feed .post .body")
    assert "<b>not bold</b>" in body.text and bob.find_elements(By.CSS_SELECTOR, "#feed .post .body b") == []  # escaped

    # Bob likes it; Alice's count updates live.
    bob.find_element(By.CSS_SELECTOR, "#feed .post .like").click()
    wait_for(lambda: alice.find_element(By.CSS_SELECTOR, "#feed .post .likes").text == "1")

    # Bob comments; Alice's comment counter updates live.
    bob.find_element(By.CSS_SELECTOR, "#feed .post .toggle-comments").click()
    bob.find_element(By.CSS_SELECTOR, "#feed .post .comment-input").send_keys("Nice post!")
    bob.find_element(By.CSS_SELECTOR, "#feed .post .comment-form button").click()
    wait_for(lambda: alice.find_element(By.CSS_SELECTOR, "#feed .post .comments").text == "1")

    # Only the author sees Delete.
    assert bob.find_element(By.CSS_SELECTOR, "#feed .post .delete").get_attribute("hidden") is not None
    assert alice.find_element(By.CSS_SELECTOR, "#feed .post .delete").get_attribute("hidden") is None


def test_validation_and_wrong_password_messages(server, two_browsers):
    from selenium.webdriver.common.by import By
    d, _ = two_browsers
    sign_up(d, server, "carol")
    d.find_element(By.ID, "logout").click()
    wait_for(lambda: d.find_element(By.ID, "auth").is_displayed())
    d.find_element(By.ID, "username").send_keys("carol")
    d.find_element(By.ID, "password").send_keys("wrong-password-1")
    d.find_element(By.CSS_SELECTOR, "button[data-action=login]").click()
    assert wait_for(lambda: d.find_element(By.ID, "auth-error").text) == "Incorrect username or password"


def test_status_dashboard_shows_numbers(server, two_browsers):
    from selenium.webdriver.common.by import By
    d, _ = two_browsers
    d.get(server + "/status")
    tiles = wait_for(lambda: d.find_elements(By.CSS_SELECTOR, ".tile"))
    labels = [t.find_element(By.CSS_SELECTOR, ".k").text.lower() for t in tiles]
    assert labels == ["uptime", "requests", "5xx error rate", "p95 latency", "live connections", "sign-ups"]
