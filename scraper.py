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

# Malaysian states for validation
MALAYSIAN_STATES = {
    "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan",
    "Pahang", "Penang", "Perak", "Perlis", "Sabah", "Sarawak",
    "Selangor", "Terengganu", "Kuala Lumpur", "Labuan", "Putrajaya"
}

# Distance patterns for extraction
DISTANCE_PATTERNS = {
    r'\b(5K|5KM)\b': '5km',
    r'\b(10K|10KM)\b': '10km',
    r'\b(21K|21KM|Half Marathon|HM)\b': '21km',
    r'\b(42K|42KM|42\.195KM|Marathon)\b': '42km',
    r'\bUltra\b': '50km+',
    r'\b(50K|50KM)\b': '50km',
    r'\b(100K|100KM)\b': '100km',
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

def extract_state_from_location(location):
    """Extract state from location string
    
    Handles formats:
    - "City, State" -> "State"
    - "Venue, City, State" -> "State"
    """
    if not location:
        return ""
    
    # Split by comma and get the last part (usually the state)
    parts = [p.strip() for p in location.split(',')]
    if len(parts) >= 2:
        potential_state = parts[-1]
        # Check if it's a known Malaysian state
        if potential_state in MALAYSIAN_STATES:
            return potential_state
        # If not, might be a city that's also a state (like Kuala Lumpur)
        if len(parts) >= 2 and parts[-2] in MALAYSIAN_STATES:
            return parts[-2]
    
    logger.debug(f"Could not extract state from location: {location}")
    return ""

def extract_distance_from_name(name):
    """Extract distance from event name
    
    Recognizes patterns like:
    - "Half Marathon", "HM" -> "21km"
    - "Marathon", "42KM" -> "42km"
    - "Ultra" -> "50km+"
    - "5K", "10K" -> "5km", "10km"
    """
    if not name:
        return ""
    
    # Try each pattern
    for pattern, distance in DISTANCE_PATTERNS.items():
        if re.search(pattern, name, re.IGNORECASE):
            logger.debug(f"Extracted distance '{distance}' from name: {name}")
            return distance
    
    logger.debug(f"Could not extract distance from name: {name}")
    return ""

def validate_url(url):
    """Validate URL format"""
    if not url:
        return False
    return url.startswith('http://') or url.startswith('https://')

def validate_date(date_str):
    """Validate date format and ensure it's current year or future
    
    Args:
        date_str: Date string in YYYY-MM-DD format
    
    Returns:
        bool: True if valid, False otherwise
    """
    from datetime import datetime
    
    if not date_str:
        return False
    
    # Check format
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return False
    
    try:
        # Parse date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        current_year = datetime.now().year
        
        # Ensure year is current or future
        if date_obj.year < current_year:
            return False
        
        return True
    except ValueError:
        return False

def validate_event(event):
    """Validate a single event
    
    Args:
        event: Event dictionary
    
    Returns:
        tuple: (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    if not event.get('name') or len(event.get('name', '')) < 3:
        errors.append("Name is missing or too short")
    
    if not event.get('date'):
        errors.append("Date is missing")
    elif not validate_date(event.get('date')):
        errors.append(f"Invalid date format or past date: {event.get('date')}")
    
    if not event.get('registration_url'):
        errors.append("Registration URL is missing")
    elif not validate_url(event.get('registration_url')):
        errors.append(f"Invalid URL format: {event.get('registration_url')}")
    
    # Optional warnings (not errors)
    if not event.get('location'):
        logger.info(f"Event '{event.get('name')}' has no location")
    
    is_valid = len(errors) == 0
    return is_valid, errors

def validate_dataset(events):
    """Validate the entire dataset and generate report
    
    Args:
        events: List of event dictionaries
    
    Returns:
        dict: Validation report with statistics
    """
    from datetime import datetime
    from collections import Counter
    
    report = {
        'total_events': len(events),
        'valid_events': 0,
        'invalid_events': 0,
        'duplicates': 0,
        'stats': {},
        'distributions': {}
    }
    
    if not events:
        report['stats']['error'] = "No events found"
        return report
    
    # Count events with each field
    report['stats']['with_names'] = sum(1 for e in events if e.get('name'))
    report['stats']['with_locations'] = sum(1 for e in events if e.get('location'))
    report['stats']['with_states'] = sum(1 for e in events if e.get('state'))
    report['stats']['with_distances'] = sum(1 for e in events if e.get('distance'))
    report['stats']['with_urls'] = sum(1 for e in events if e.get('registration_url'))
    
    # Calculate percentages
    total = len(events)
    report['stats']['state_extraction_rate'] = (report['stats']['with_states'] / total * 100) if total > 0 else 0
    report['stats']['distance_extraction_rate'] = (report['stats']['with_distances'] / total * 100) if total > 0 else 0
    
    # Get date range
    dates = [e.get('date') for e in events if e.get('date')]
    if dates:
        report['stats']['date_range'] = f"{min(dates)} to {max(dates)}"
        
        # Count unique months
        months = set(d[:7] for d in dates)  # YYYY-MM format
        report['stats']['months_covered'] = len(months)
    
    # Check for duplicates (same name + date)
    event_keys = [(e.get('name'), e.get('date')) for e in events]
    duplicates = [k for k, count in Counter(event_keys).items() if count > 1]
    report['duplicates'] = len(duplicates)
    
    # State distribution
    states = [e.get('state') for e in events if e.get('state')]
    report['distributions']['states'] = dict(Counter(states).most_common(10))
    
    # Distance distribution
    distances = [e.get('distance') for e in events if e.get('distance')]
    report['distributions']['distances'] = dict(Counter(distances).most_common())
    
    # Validate each event
    for event in events:
        is_valid, errors = validate_event(event)
        if is_valid:
            report['valid_events'] += 1
        else:
            report['invalid_events'] += 1
            logger.warning(f"Invalid event: {event.get('name')} - Errors: {', '.join(errors)}")
    
    return report

def print_validation_report(report):
    """Print a formatted validation report"""
    print("\n" + "="*50)
    print(" Dataset Validation Report")
    print("="*50)
    
    stats = report.get('stats', {})
    total = report.get('total_events', 0)
    
    print(f"\n✓ Total events: {total}")
    if 'date_range' in stats:
        print(f"✓ Date range: {stats['date_range']}")
    if 'months_covered' in stats:
        print(f"✓ Months covered: {stats['months_covered']}")
    
    print(f"✓ Events with locations: {stats.get('with_locations', 0)} ({stats.get('with_locations', 0)/total*100:.1f}%)")
    print(f"✓ Events with states: {stats.get('with_states', 0)} ({stats.get('state_extraction_rate', 0):.1f}%)")
    print(f"✓ Events with distances: {stats.get('with_distances', 0)} ({stats.get('distance_extraction_rate', 0):.1f}%)")
    print(f"✓ Events with URLs: {stats.get('with_urls', 0)} ({stats.get('with_urls', 0)/total*100:.1f}%)")
    
    if report.get('duplicates', 0) > 0:
        print(f"⚠ Duplicates found: {report['duplicates']}")
    else:
        print(f"✓ No duplicates found")
    
    print(f"\n✓ Valid events: {report.get('valid_events', 0)}")
    if report.get('invalid_events', 0) > 0:
        print(f"⚠ Invalid events: {report['invalid_events']}")
    
    # State distribution
    if 'states' in report.get('distributions', {}):
        print(f"\n=== State Distribution (Top 10) ===")
        for state, count in report['distributions']['states'].items():
            print(f"{state}: {count} events")
    
    # Distance distribution
    if 'distances' in report.get('distributions', {}):
        print(f"\n=== Distance Distribution ===")
        for distance, count in report['distributions']['distances'].items():
            print(f"{distance}: {count} events")
    
    print("\n" + "="*50)

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
                    
                    # Extract state and distance
                    state = extract_state_from_location(location)
                    distance = extract_distance_from_name(event_name)
                    
                    # Parse date
                    full_date = parse_date(day, month_abbr, current_year)
                    
                    if full_date and event_name:
                        event = {
                            "name": event_name,
                            "location": location,
                            "state": state,
                            "distance": distance,
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
        keys = ["name", "location", "state", "distance", "date", "description", "registration_url"]
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
            return
        
        # Validate dataset
        validation_report = validate_dataset(event_data)
        
        # Save the data
        save_to_json(event_data)
        save_to_csv(event_data)
        
        print(f"\n Scraping completed")
        print(f"Total events extracted: {len(event_data)}")
        print(f"Data saved to events.json and events.csv")
        
        # Print validation report
        print_validation_report(validation_report)
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        print(f"\n Scraping failed: {e}")
        raise

if __name__ == "__main__":
    main()