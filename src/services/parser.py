"""
HTML parser service for extracting event data from scraped pages.
"""
import re
from typing import List, Optional, Dict

from bs4 import BeautifulSoup

from src.config import get_logger, MONTHS, MALAYSIAN_STATES, DISTANCE_PATTERNS
from src.models import Event

logger = get_logger(__name__)


def extract_location_from_text(text: str) -> str:
    """Extract location from text in format 'Event Name (Location)'.
    
    Args:
        text: Event text containing location in parentheses
        
    Returns:
        Location string or empty string if not found
    """
    match = re.search(r'\(([^)]+)\)\s*(?:⭐)?$', text)
    if match:
        return match.group(1).strip()
    return ""


def extract_event_name_from_text(text: str) -> str:
    """Extract event name from text, removing location and star emoji.
    
    Args:
        text: Full event text
        
    Returns:
        Clean event name
    """
    text = re.sub(r'\s*\([^)]+\)\s*(?:⭐)?$', '', text)
    return text.strip()


def parse_date(day_str: str, month_str: str, year: int) -> Optional[str]:
    """Parse date components into YYYY-MM-DD format.
    
    Args:
        day_str: Day as string (e.g., "15")
        month_str: Month abbreviation (e.g., "Nov")
        year: Year as integer
        
    Returns:
        Date string in YYYY-MM-DD format or None if parsing fails
    """
    try:
        day = int(day_str)
        month_num = MONTHS.get(month_str[:3], "00")
        return f"{year}-{month_num}-{str(day).zfill(2)}"
    except (ValueError, AttributeError):
        logger.warning(f"Failed to parse date: day={day_str}, month={month_str}, year={year}")
        return None


def extract_state_from_location(location: str) -> str:
    """Extract Malaysian state from location string.
    
    Handles formats:
    - "City, State" -> "State"
    - "Venue, City, State" -> "State"
    
    Args:
        location: Location string
        
    Returns:
        State name or empty string if not found
    """
    if not location:
        return ""
    
    parts = [p.strip() for p in location.split(',')]
    if len(parts) >= 2:
        potential_state = parts[-1]
        if potential_state in MALAYSIAN_STATES:
            return potential_state
        # Check if second-to-last is a state (e.g., "Venue, Kuala Lumpur, Malaysia")
        if len(parts) >= 2 and parts[-2] in MALAYSIAN_STATES:
            return parts[-2]
    
    logger.debug(f"Could not extract state from location: {location}")
    return ""


def extract_distance_from_name(name: str) -> str:
    """Extract distance from event name.
    
    Recognizes patterns like:
    - "Half Marathon", "HM" -> "21km"
    - "Marathon", "42KM" -> "42km"
    - "Ultra" -> "50km+"
    - "5K", "10K" -> "5km", "10km"
    
    Args:
        name: Event name
        
    Returns:
        Normalized distance or empty string if not found
    """
    if not name:
        return ""
    
    for pattern, distance in DISTANCE_PATTERNS.items():
        if re.search(pattern, name, re.IGNORECASE):
            logger.debug(f"Extracted distance '{distance}' from name: {name}")
            return distance
    
    logger.debug(f"Could not extract distance from name: {name}")
    return ""


def scrape_event_data(soup: BeautifulSoup) -> List[Event]:
    """Main scraping logic for extracting events from page.
    
    Args:
        soup: BeautifulSoup object of the parsed page
        
    Returns:
        List of Event objects
    """
    events: List[Event] = []
    skipped_count = 0
    
    logger.info("Starting event extraction")
    
    # Find all elements in the page
    all_elements = soup.find_all(['b', 'div'])
    
    current_month: Optional[str] = None
    current_year: Optional[int] = None
    
    for element in all_elements:
        # Check if this is a month header: <b><u><span>MONTH YEAR</span></u></b>
        if element.name == 'b':
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
                            
                            month_abbr = month_name[:3].title()
                            if month_abbr in MONTHS:
                                current_month = month_abbr
                                current_year = year
                                logger.info(f"Found month header: {month_name} {year}")
                        except (ValueError, IndexError):
                            logger.warning(f"Failed to parse month header: {month_year_text}")
        
        # Check if this is an event entry: <div>DD Mon - <a href="...">Event Name (Location)</a></div>
        elif element.name == 'div' and current_month and current_year:
            text = element.get_text(strip=True)
            
            # Look for date pattern: "DD Mon -"
            date_match = re.match(r'^(\d{1,2})\s+(\w{3})\s*-\s*(.+)$', text)
            if date_match:
                day = date_match.group(1)
                month_abbr = date_match.group(2)
                
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
                        event = Event(
                            name=event_name,
                            location=location,
                            state=state,
                            distance=distance,
                            date=full_date,
                            description="",
                            registration_url=registration_url
                        )
                        events.append(event)
                        logger.debug(f"Extracted event: {event_name} on {full_date}")
                    else:
                        skipped_count += 1
                        logger.warning(f"Skipped event due to missing data: {text[:50]}")
    
    logger.info(f"Extraction complete. Found {len(events)} events, skipped {skipped_count}")
    return events
