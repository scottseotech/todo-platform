from selenium.webdriver.common.by import By
import pickle
import os
from pathlib import Path

selenium_cookies_path = os.path.expanduser("~/selenium_cookies.pkl")
login_url = os.environ.get("SEL_LOGIN_URL")

def _load_cookies(driver):
    driver.get(login_url)

    with open(selenium_cookies_path, "rb") as f:
        cookies = pickle.load(f)

    for cookie in cookies:
        # Selenium doesn't like sameSite=None as string sometimes
        if 'sameSite' in cookie:
            del cookie['sameSite']
        driver.add_cookie(cookie)

    # Refresh to apply the cookies
    driver.refresh()

def _save_cookies(driver):
    with open(selenium_cookies_path, "wb") as file:
        pickle.dump(driver.get_cookies(), file)

def _do_login(driver):
    driver.get(login_url)

    username = os.getenv("SEL_USERNAME")
    password = os.getenv("SEL_PASSWORD")

    username_field = driver.find_element("id", "username")
    password_field = driver.find_element("id", "password")

    username_field.send_keys(username)
    password_field.send_keys(password)

    login_button = driver.find_element("id", "Login")
    login_button.click()

    _save_cookies(driver)

def _ensure_login(driver):
    p = Path(selenium_cookies_path)

    if p.is_file():
        _load_cookies(driver)
    else:
        _do_login(driver)

def test_page_1(driver):
    _ensure_login(driver)

    driver.get("somewhere")

    print("Testing foo")
