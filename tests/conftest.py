"""Pytest configuration and shared fixtures"""
import pytest
from bs4 import BeautifulSoup


@pytest.fixture
def sample_event():
    """Sample valid event for testing"""
    return {
        "name": "Test Marathon",
        "location": "Test City, Selangor",
        "state": "Selangor",
        "distance": "42km",
        "date": "2026-06-15",
        "description": "",
        "registration_url": "https://example.com/event"
    }


@pytest.fixture
def sample_events_list():
    """List of sample events for dataset testing"""
    return [
        {
            "name": "Kota Belud Half Marathon",
            "location": "Kota Belud, Sabah",
            "state": "Sabah",
            "distance": "21km",
            "date": "2026-11-08",
            "description": "",
            "registration_url": "https://checkpointspot.asia/event/test1"
        },
        {
            "name": "Malaysia Ultra",
            "location": "Kuala Lumpur",
            "state": "Kuala Lumpur",
            "distance": "50km+",
            "date": "2026-10-24",
            "description": "",
            "registration_url": "https://checkpointspot.asia/event/test2"
        },
        {
            "name": "5K Speed Run",
            "location": "KLCC, Kuala Lumpur",
            "state": "Kuala Lumpur",
            "distance": "5km",
            "date": "2026-09-19",
            "description": "",
            "registration_url": "https://www.heyjom.com/event/test3"
        }
    ]


@pytest.fixture
def mock_html_month_header():
    """Mock HTML for a month header"""
    html = """
    <b><u><span>NOV 2026</span></u></b>
    """
    return BeautifulSoup(html, "html.parser")


@pytest.fixture
def mock_html_event():
    """Mock HTML for a single event"""
    html = """
    <div>08 Nov - <a href="https://checkpointspot.asia/event/test" target="_blank">
    Kota Belud Half Marathon (Kota Belud, Sabah)</a></div>
    """
    return BeautifulSoup(html, "html.parser")


@pytest.fixture
def mock_html_full_page():
    """Mock HTML for a full page with multiple events"""
    html = """
    <html>
    <body>
        <b><u><span>NOV 2026</span></u></b>
        <div>08 Nov - <a href="https://checkpointspot.asia/event/test1">Kota Belud Half Marathon (Kota Belud, Sabah)</a></div>
        <div>15 Nov - <a href="https://checkpointspot.asia/event/test2">Penang Bridge Marathon (Penang)</a></div>
        
        <b><u><span>OCT 2026</span></u></b>
        <div>24 Oct - <a href="https://checkpointspot.asia/event/test3">Malaysia Taman Negara Ultra (Jerantut, Pahang)</a></div>
        <div>04 Oct - <a href="https://www.kl-marathon.com/">Kuala Lumpur Marathon - 42KM (Kuala Lumpur)</a></div>
    </body>
    </html>
    """
    return BeautifulSoup(html, "html.parser")
