"""
Data models for the scraper.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any


@dataclass
class Event:
    """Represents a running event scraped from the website.
    
    Attributes:
        name: Event name (e.g., "Kuala Lumpur Marathon")
        location: Full location string (e.g., "KLCC, Kuala Lumpur")
        date: Date in YYYY-MM-DD format
        registration_url: URL for event registration
        state: Malaysian state (e.g., "Selangor", "Kuala Lumpur")
        distance: Normalized distance (e.g., "21km", "42km")
        description: Optional event description
    """
    name: str
    location: str
    date: str
    registration_url: str
    state: str = ""
    distance: str = ""
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create an Event from a dictionary."""
        return cls(
            name=data.get("name", ""),
            location=data.get("location", ""),
            date=data.get("date", ""),
            registration_url=data.get("registration_url", ""),
            state=data.get("state", ""),
            distance=data.get("distance", ""),
            description=data.get("description", ""),
        )
    
    def __str__(self) -> str:
        """String representation for logging."""
        return f"{self.name} ({self.date}) - {self.location}"
