"""
Validation utilities for events and datasets.
"""
import re
from datetime import datetime
from collections import Counter
from typing import List, Dict, Any, Tuple

from src.config import get_logger
from src.models import Event

logger = get_logger(__name__)


def validate_url(url: str) -> bool:
    """Validate URL format.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid HTTP/HTTPS URL, False otherwise
    """
    if not url:
        return False
    return url.startswith('http://') or url.startswith('https://')


def validate_date(date_str: str) -> bool:
    """Validate date format and ensure it's current year or future.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        True if valid and not in the past, False otherwise
    """
    if not date_str:
        return False
    
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return False
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        current_year = datetime.now().year
        
        if date_obj.year < current_year:
            return False
        
        return True
    except ValueError:
        return False


def validate_event(event: Event | Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a single event.
    
    Args:
        event: Event object or dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors: List[str] = []
    
    # Handle both Event objects and dicts
    if isinstance(event, Event):
        name = event.name
        date = event.date
        registration_url = event.registration_url
        location = event.location
    else:
        name = event.get('name', '')
        date = event.get('date', '')
        registration_url = event.get('registration_url', '')
        location = event.get('location', '')
    
    # Check required fields
    if not name or len(name) < 3:
        errors.append("Name is missing or too short")
    
    if not date:
        errors.append("Date is missing")
    elif not validate_date(date):
        errors.append(f"Invalid date format or past date: {date}")
    
    if not registration_url:
        errors.append("Registration URL is missing")
    elif not validate_url(registration_url):
        errors.append(f"Invalid URL format: {registration_url}")
    
    # Optional warnings (not errors)
    if not location:
        logger.info(f"Event '{name}' has no location")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def validate_dataset(events: List[Event] | List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate the entire dataset and generate a report.
    
    Args:
        events: List of Event objects or dictionaries
        
    Returns:
        Validation report with statistics
    """
    report: Dict[str, Any] = {
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
    
    # Helper to get field value from Event or dict
    def get_field(e, field):
        if isinstance(e, Event):
            return getattr(e, field, '')
        return e.get(field, '')
    
    # Count events with each field
    report['stats']['with_names'] = sum(1 for e in events if get_field(e, 'name'))
    report['stats']['with_locations'] = sum(1 for e in events if get_field(e, 'location'))
    report['stats']['with_states'] = sum(1 for e in events if get_field(e, 'state'))
    report['stats']['with_distances'] = sum(1 for e in events if get_field(e, 'distance'))
    report['stats']['with_urls'] = sum(1 for e in events if get_field(e, 'registration_url'))
    
    # Calculate percentages
    total = len(events)
    report['stats']['state_extraction_rate'] = (report['stats']['with_states'] / total * 100) if total > 0 else 0
    report['stats']['distance_extraction_rate'] = (report['stats']['with_distances'] / total * 100) if total > 0 else 0
    
    # Get date range
    dates = [get_field(e, 'date') for e in events if get_field(e, 'date')]
    if dates:
        report['stats']['date_range'] = f"{min(dates)} to {max(dates)}"
        months = set(d[:7] for d in dates)
        report['stats']['months_covered'] = len(months)
    
    # Check for duplicates (same name + date)
    event_keys = [(get_field(e, 'name'), get_field(e, 'date')) for e in events]
    duplicates = [k for k, count in Counter(event_keys).items() if count > 1]
    report['duplicates'] = len(duplicates)
    
    # State distribution
    states = [get_field(e, 'state') for e in events if get_field(e, 'state')]
    report['distributions']['states'] = dict(Counter(states).most_common(10))
    
    # Distance distribution
    distances = [get_field(e, 'distance') for e in events if get_field(e, 'distance')]
    report['distributions']['distances'] = dict(Counter(distances).most_common())
    
    # Validate each event
    for event in events:
        is_valid, errors = validate_event(event)
        if is_valid:
            report['valid_events'] += 1
        else:
            report['invalid_events'] += 1
            name = get_field(event, 'name')
            logger.warning(f"Invalid event: {name} - Errors: {', '.join(errors)}")
    
    return report


def print_validation_report(report: Dict[str, Any]) -> None:
    """Print a formatted validation report.
    
    Args:
        report: Validation report from validate_dataset()
    """
    print("\n" + "=" * 50)
    print(" Dataset Validation Report")
    print("=" * 50)
    
    stats = report.get('stats', {})
    total = report.get('total_events', 0)
    
    print(f"\n✓ Total events: {total}")
    if 'date_range' in stats:
        print(f"✓ Date range: {stats['date_range']}")
    if 'months_covered' in stats:
        print(f"✓ Months covered: {stats['months_covered']}")
    
    if total > 0:
        print(f"✓ Events with locations: {stats.get('with_locations', 0)} ({stats.get('with_locations', 0)/total*100:.1f}%)")
        print(f"✓ Events with states: {stats.get('with_states', 0)} ({stats.get('state_extraction_rate', 0):.1f}%)")
        print(f"✓ Events with distances: {stats.get('with_distances', 0)} ({stats.get('distance_extraction_rate', 0):.1f}%)")
        print(f"✓ Events with URLs: {stats.get('with_urls', 0)} ({stats.get('with_urls', 0)/total*100:.1f}%)")
    
    if report.get('duplicates', 0) > 0:
        print(f"⚠ Duplicates found: {report['duplicates']}")
    else:
        print("✓ No duplicates found")
    
    print(f"\n✓ Valid events: {report.get('valid_events', 0)}")
    if report.get('invalid_events', 0) > 0:
        print(f"⚠ Invalid events: {report['invalid_events']}")
    
    # State distribution
    if 'states' in report.get('distributions', {}):
        print("\n=== State Distribution (Top 10) ===")
        for state, count in report['distributions']['states'].items():
            print(f"{state}: {count} events")
    
    # Distance distribution
    if 'distances' in report.get('distributions', {}):
        print("\n=== Distance Distribution ===")
        for distance, count in report['distributions']['distances'].items():
            print(f"{distance}: {count} events")
    
    print("\n" + "=" * 50)
