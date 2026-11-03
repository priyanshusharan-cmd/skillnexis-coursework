"""Shared fixtures: a headless browser per test and a running Demo Shop.

Browser choice: BROWSER=firefox (default) or chrome. Set FIREFOX_BIN / GECKODRIVER or
CHROMEDRIVER when the binaries are not on PATH. BASE_URL points at an already
running shop; if unset, the shop is started on a free port for the test session.
"""
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest
from selenium import webdriver

HERE = Path(__file__).resolve().parent
SHOP = HERE.parent / "demo-shop" / "server.js"


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def base_url():
    if os.environ.get("BASE_URL"):
        yield os.environ["BASE_URL"].rstrip("/")
        return
    port = _free_port()
    proc = subprocess.Popen(["node", str(SHOP)], env={**os.environ, "PORT": str(port)}, stdout=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            urllib.request.urlopen(url + "/api/health", timeout=1)
            break
        except OSError:
            time.sleep(0.1)
    yield url
    proc.terminate()
    proc.wait(timeout=5)


def _make_driver():
    browser = os.environ.get("BROWSER", "firefox").lower()
    if browser == "chrome":
        opts = webdriver.ChromeOptions()
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1280,900")
        service = webdriver.ChromeService(executable_path=os.environ["CHROMEDRIVER"]) if os.environ.get("CHROMEDRIVER") else webdriver.ChromeService()
        return webdriver.Chrome(options=opts, service=service)
    opts = webdriver.FirefoxOptions()
    opts.add_argument("-headless")
    if os.environ.get("FIREFOX_BIN"):
        opts.binary_location = os.environ["FIREFOX_BIN"]
    service = webdriver.FirefoxService(executable_path=os.environ["GECKODRIVER"]) if os.environ.get("GECKODRIVER") else webdriver.FirefoxService()
    d = webdriver.Firefox(options=opts, service=service)
    d.set_window_size(1280, 900)
    return d


@pytest.fixture
def driver(request):
    d = _make_driver()
    yield d
    # Keep a screenshot of every failure for the bug report.
    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        out = HERE.parent / "results" / "screenshots"
        out.mkdir(parents=True, exist_ok=True)
        d.save_screenshot(str(out / f"{request.node.name}.png"))
    d.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
