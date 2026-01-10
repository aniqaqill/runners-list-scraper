"""
File exporter service for saving events to JSON and CSV files.
"""
import json
import csv
from typing import List, Dict, Any
from pathlib import Path

from src.config import get_logger, DEFAULT_JSON_OUTPUT, DEFAULT_CSV_OUTPUT
from src.models import Event

logger = get_logger(__name__)


def save_to_json(
    events: List[Event] | List[Dict[str, Any]],
    filename: str = DEFAULT_JSON_OUTPUT
) -> Path:
    """Save events to a JSON file.
    
    Args:
        events: List of Event objects or dictionaries
        filename: Output filename (default: events.json)
        
    Returns:
        Path to the saved file
        
    Raises:
        IOError: If file writing fails
    """
    # Convert Event objects to dicts if needed
    events_data = []
    for event in events:
        if isinstance(event, Event):
            events_data.append(event.to_dict())
        else:
            events_data.append(event)
    
    try:
        filepath = Path(filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(events_data, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved {len(events)} events to {filename}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save JSON: {e}")
        raise IOError(f"Failed to save JSON file: {e}")


def save_to_csv(
    events: List[Event] | List[Dict[str, Any]],
    filename: str = DEFAULT_CSV_OUTPUT
) -> Path:
    """Save events to a CSV file.
    
    Args:
        events: List of Event objects or dictionaries
        filename: Output filename (default: events.csv)
        
    Returns:
        Path to the saved file
        
    Raises:
        IOError: If file writing fails
    """
    # Convert Event objects to dicts if needed
    events_data = []
    for event in events:
        if isinstance(event, Event):
            events_data.append(event.to_dict())
        else:
            events_data.append(event)
    
    keys = ["name", "location", "state", "distance", "date", "description", "registration_url"]
    
    try:
        filepath = Path(filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(events_data)
        logger.info(f"Saved {len(events)} events to {filename}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save CSV: {e}")
        raise IOError(f"Failed to save CSV file: {e}")
