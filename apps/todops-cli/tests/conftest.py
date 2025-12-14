"""Pytest configuration and fixtures for todops tests."""

import pytest
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

@pytest.fixture(scope="session", autouse=True)
def load_test_env():
    """Load .env file automatically for all tests.

    This fixture runs once per test session and automatically loads
    environment variables from the .env file in the project root.
    """
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"\n✓ Loaded environment variables from {env_path}")
    else:
        print(f"\n⚠ Warning: .env file not found at {env_path}")

# @pytest.fixture(scope="function")
# def driver():
#     # Setup: Initialize the WebDriver
#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service)
#     driver.implicitly_wait(10) # Set implicit wait
#
#     yield driver
#
#     # Teardown: Quit the browser after the test function runs
#     driver.quit()

@pytest.fixture(scope="function")
def driver():
    # Setup: Initialize the WebDriver
    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service)
    driver.implicitly_wait(10)  # Set implicit wait

    yield driver

    # Teardown: Quit the browser after the test function runs
    driver.quit()
