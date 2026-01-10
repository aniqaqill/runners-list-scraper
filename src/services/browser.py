"""
Browser service for Selenium WebDriver setup and page fetching.
"""
import time
from typing import Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from src.config import get_logger

logger = get_logger(__name__)


def setup_driver() -> webdriver.Chrome:
    """Set up Selenium WebDriver with headless Chrome options.
    
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
        
    Raises:
        Exception: If WebDriver initialization fails
    """
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    try:
        driver = webdriver.Chrome(options=options)
        logger.info("Chrome WebDriver initialized successfully")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {e}")
        raise


def fetch_page(url: str, wait_time: int = 5) -> BeautifulSoup:
    """Fetch a page using Selenium and return a BeautifulSoup object.
    
    Args:
        url: URL to fetch
        wait_time: Time to wait for JavaScript rendering (seconds)
        
    Returns:
        BeautifulSoup: Parsed HTML
        
    Raises:
        Exception: If page fetching fails
    """
    driver: Optional[webdriver.Chrome] = None
    try:
        driver = setup_driver()
        logger.info(f"Fetching URL: {url}")
        driver.get(url)
        
        # Wait for page to load (JavaScript rendering)
        time.sleep(wait_time)
        
        # Get page source and parse
        soup = BeautifulSoup(driver.page_source, "html.parser")
        logger.info("Page fetched and parsed successfully")
        
        return soup
    except Exception as e:
        logger.error(f"Error fetching page: {e}")
        raise
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver closed")
