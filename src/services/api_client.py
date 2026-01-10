"""
API client service for syncing events to the backend API.
"""
import time
from typing import List, Dict, Any

import requests

from src.config import get_logger
from src.models import Event

logger = get_logger(__name__)


class APIError(Exception):
    """Custom exception for API-related errors."""
    pass


class AuthenticationError(APIError):
    """Raised when API authentication fails."""
    pass


def send_to_api(
    events: List[Event] | List[Dict[str, Any]],
    api_url: str,
    api_key: str,
    max_retries: int = 3
) -> Dict[str, Any]:
    """Send events to the API internal sync endpoint.
    
    Args:
        events: List of Event objects or dictionaries
        api_url: URL of the internal sync endpoint
        api_key: API key for authentication
        max_retries: Maximum number of retry attempts (default: 3)
        
    Returns:
        Response dict with success, inserted, updated counts
        
    Raises:
        AuthenticationError: If API key is invalid
        APIError: If sync fails after all retries
    """
    headers = {
        "Content-Type": "application/json",
        "X-Internal-Token": api_key
    }
    
    # Convert Event objects to dicts if needed
    events_data = []
    for event in events:
        if isinstance(event, Event):
            events_data.append(event.to_dict())
        else:
            events_data.append(event)
    
    payload = {"events": events_data}
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Sending {len(events)} events to API (attempt {attempt + 1}/{max_retries})")
            
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # Check for authentication errors (don't retry)
            if response.status_code == 401:
                error_msg = response.json().get('error', 'Unauthorized')
                logger.error(f"API authentication failed: {error_msg}")
                raise AuthenticationError(f"API authentication failed: {error_msg}")
            
            # Check for success
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(
                        f"Successfully synced events: "
                        f"inserted={result.get('inserted', 0)}, "
                        f"updated={result.get('updated', 0)}, "
                        f"total={result.get('total', 0)}"
                    )
                    return result
                else:
                    error_msg = result.get('error', 'Unknown error')
                    logger.error(f"API returned error: {error_msg}")
                    raise APIError(f"API error: {error_msg}")
            
            # Server error - may retry
            if response.status_code >= 500:
                logger.warning(f"Server error {response.status_code}, will retry...")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            
            # Other client errors - don't retry
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
            raise APIError(f"API request failed with status {response.status_code}")
            
        except requests.exceptions.Timeout:
            logger.warning("Request timeout, will retry...")
            time.sleep(2 ** attempt)
            continue
            
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error: {e}, will retry...")
            time.sleep(2 ** attempt)
            continue
            
        except AuthenticationError:
            # Don't retry auth errors
            raise
            
        except APIError:
            if attempt >= max_retries - 1:
                raise
            logger.warning("API error, will retry...")
            time.sleep(2 ** attempt)
            continue
            
        except Exception as e:
            if attempt >= max_retries - 1:
                raise APIError(f"Unexpected error: {e}")
            logger.warning(f"Error: {e}, will retry...")
            time.sleep(2 ** attempt)
            continue
    
    raise APIError(f"Failed to sync events after {max_retries} attempts")
