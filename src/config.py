"""
Configuration constants and environment variable loading for the scraper.
"""
import os
import logging
from typing import Dict, Set

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


# ============================================================================
# Constants
# ============================================================================

# Month mapping for date parsing
MONTHS: Dict[str, str] = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
    "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
    "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
}

# Malaysian states for validation
MALAYSIAN_STATES: Set[str] = {
    "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan",
    "Pahang", "Penang", "Perak", "Perlis", "Sabah", "Sarawak",
    "Selangor", "Terengganu", "Kuala Lumpur", "Labuan", "Putrajaya"
}

# Distance patterns for extraction (regex pattern -> normalized distance)
DISTANCE_PATTERNS: Dict[str, str] = {
    r'\b(5K|5KM)\b': '5km',
    r'\b(10K|10KM)\b': '10km',
    r'\b(21K|21KM|Half Marathon|HM)\b': '21km',
    r'\b(42K|42KM|42\.195KM|Marathon)\b': '42km',
    r'\bUltra\b': '50km+',
    r'\b(50K|50KM)\b': '50km',
    r'\b(100K|100KM)\b': '100km',
}

# Default output filenames
DEFAULT_JSON_OUTPUT = "events.json"
DEFAULT_CSV_OUTPUT = "events.csv"


# ============================================================================
# Environment Variables
# ============================================================================

def get_api_url() -> str | None:
    """Get the API URL from environment variables."""
    return os.environ.get("API_URL")


def get_api_key() -> str | None:
    """Get the API key from environment variables."""
    return os.environ.get("API_KEY")


def get_scrape_url() -> str | None:
    """Get the scraping URL from environment variables."""
    return os.environ.get("SCRAPE_URL")


def is_api_configured() -> bool:
    """Check if API credentials are configured."""
    return bool(get_api_url() and get_api_key())
