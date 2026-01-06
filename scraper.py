from bs4 import BeautifulSoup
import json
import csv
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Month mapping for date parsing
MONTHS = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
    "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
    "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
}

def setup_driver():
    """Set up Selenium WebDriver with options"""
    options = Options()
    options.add_argument('--headless') 
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=options)
        logger.info("Chrome WebDriver initialized successfully")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {e}")
        raise

def fetch_page(url, wait_time=5):
    """Fetch the page using Selenium and return BeautifulSoup object"""
    driver = None
    try:
        driver = setup_driver()
        logger.info(f"Fetching URL: {url}")
        driver.get(url)
        
        # Wait for page to load
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

def extract_location_from_text(text):
    """Extract location from text in format 'Event Name (Location)'"""
    # Look for text in parentheses at the end
    match = re.search(r'\(([^)]+)\)\s*(?:⭐)?$', text)
    if match:
        return match.group(1).strip()
    return ""

def extract_event_name_from_text(text):
    """Extract event name from text, removing location and star"""
    # Remove location in parentheses and star emoji
    text = re.sub(r'\s*\([^)]+\)\s*(?:⭐)?$', '', text)
    return text.strip()

def parse_date(day_str, month_str, year):
    """Parse date components into YYYY-MM-DD format"""
    try:
        day = int(day_str)
        month_num = MONTHS.get(month_str[:3], "00")
        return f"{year}-{month_num}-{str(day).zfill(2)}"
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse date: day={day_str}, month={month_str}, year={year}")
        return None

def scrape_event_data(soup):
    """Main scraping logic for 2026 events page"""
    events = []
    skipped_count = 0
    
    logger.info("Starting event extraction")
    
    # Find all elements in the page
    all_elements = soup.find_all(['b', 'div'])
    
    current_month = None
    current_year = None
    
    for element in all_elements:
        # Check if this is a month header: <b><u><span>MONTH YEAR</span></u></b>
        if element.name == 'b':
            # Look for underlined span inside
            u_tag = element.find('u')
            if u_tag:
                span_tag = u_tag.find('span')
                if span_tag:
                    month_year_text = span_tag.get_text(strip=True)
                    
                    # Try to parse "NOV 2026" or "NOVEMBER 2026" format
                    parts = month_year_text.split()
                    if len(parts) == 2:
                        try:
                            month_name = parts[0]
                            year = int(parts[1])
                            
                            # Convert month name to number
                            month_abbr = month_name[:3].title()
                            if month_abbr in MONTHS:
                                current_month = month_abbr
                                current_year = year
                                logger.info(f"Found month header: {month_name} {year}")
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Failed to parse month header: {month_year_text}")
        
        # Check if this is an event entry: <div>DD Mon - <a href="...">Event Name (Location)</a></div>
        elif element.name == 'div' and current_month and current_year:
            text = element.get_text(strip=True)
            
            # Look for date pattern: "DD Mon -"
            date_match = re.match(r'^(\d{1,2})\s+(\w{3})\s*-\s*(.+)$', text)
            if date_match:
                day = date_match.group(1)
                month_abbr = date_match.group(2)
                rest_of_text = date_match.group(3)
                
                # Find the link
                link = element.find('a')
                if link:
                    event_text = link.get_text(strip=True)
                    registration_url = link.get('href', '')
                    
                    # Extract name and location
                    event_name = extract_event_name_from_text(event_text)
                    location = extract_location_from_text(event_text)
                    
                    # Parse date
                    full_date = parse_date(day, month_abbr, current_year)
                    
                    if full_date and event_name:
                        event = {
                            "name": event_name,
                            "location": location,
                            "date": full_date,
                            "description": "",
                            "registration_url": registration_url
                        }
                        events.append(event)
                        logger.debug(f"Extracted event: {event_name} on {full_date}")
                    else:
                        skipped_count += 1
                        logger.warning(f"Skipped event due to missing data: {text[:50]}")
    
    logger.info(f"Extraction complete. Found {len(events)} events, skipped {skipped_count}")
    return events

def save_to_json(events, filename="events.json"):
    """Save events to JSON file"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved {len(events)} events to {filename}")
    except Exception as e:
        logger.error(f"Failed to save JSON: {e}")
        raise

def save_to_csv(events, filename="events.csv"):
    """Save events to CSV file"""
    try:
        keys = ["name", "location", "date", "description", "registration_url"]
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(events)
        logger.info(f"Saved {len(events)} events to {filename}")
    except Exception as e:
        logger.error(f"Failed to save CSV: {e}")
        raise

def main():
    """Main execution function"""
    try:
        # Fetch and parse the page
        url = "https://pm1.blogspot.com/p/running-event-2026.html"
        soup = fetch_page(url)
        
        # Extract event data
        event_data = scrape_event_data(soup)
        
        if not event_data:
            logger.warning("No events were extracted! Check the HTML structure.")
        
        # Save the data
        save_to_json(event_data)
        save_to_csv(event_data)
        
        print(f"\n Scraping completed")
        print(f"Total events extracted: {len(event_data)}")
        print(f"Data saved to events.json and events.csv")
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        print(f"\n Scraping failed: {e}")
        raise

if __name__ == "__main__":
    main()