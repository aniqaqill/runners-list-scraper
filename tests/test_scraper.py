"""Unit and integration tests for the scraper"""
import pytest
from datetime import datetime
import sys
import os

# Add parent directory to path to import scraper
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scraper


class TestDateParsing:
    """Tests for parse_date function"""
    
    def test_parse_date_valid(self):
        result = scraper.parse_date("15", "Nov", 2026)
        assert result == "2026-11-15"
    
    def test_parse_date_single_digit_day(self):
        result = scraper.parse_date("5", "Jan", 2026)
        assert result == "2026-01-05"
    
    def test_parse_date_invalid_day(self):
        result = scraper.parse_date("invalid", "Nov", 2026)
        assert result is None
    
    def test_parse_date_invalid_month(self):
        result = scraper.parse_date("15", "InvalidMonth", 2026)
        assert result == "2026-00-15"  # Returns 00 for invalid month


class TestLocationExtraction:
    """Tests for extract_location_from_text function"""
    
    def test_extract_location_with_parentheses(self):
        text = "Kota Belud Half Marathon (Kota Belud, Sabah)"
        result = scraper.extract_location_from_text(text)
        assert result == "Kota Belud, Sabah"
    
    def test_extract_location_with_star(self):
        text = "5K Malaysia Speed (KLCC, Kuala Lumpur) ⭐"
        result = scraper.extract_location_from_text(text)
        assert result == "KLCC, Kuala Lumpur"
    
    def test_extract_location_missing(self):
        text = "Event Name Without Location"
        result = scraper.extract_location_from_text(text)
        assert result == ""


class TestEventNameExtraction:
    """Tests for extract_event_name_from_text function"""
    
    def test_extract_name_with_location(self):
        text = "Kota Belud Half Marathon (Kota Belud, Sabah)"
        result = scraper.extract_event_name_from_text(text)
        assert result == "Kota Belud Half Marathon"
    
    def test_extract_name_with_star(self):
        text = "5K Malaysia Speed (KLCC, Kuala Lumpur) ⭐"
        result = scraper.extract_event_name_from_text(text)
        assert result == "5K Malaysia Speed"
    
    def test_extract_name_without_location(self):
        text = "Simple Event Name"
        result = scraper.extract_event_name_from_text(text)
        assert result == "Simple Event Name"


class TestStateExtraction:
    """Tests for extract_state_from_location function"""
    
    def test_extract_state_city_state_format(self):
        location = "Kota Belud, Sabah"
        result = scraper.extract_state_from_location(location)
        assert result == "Sabah"
    
    def test_extract_state_venue_city_state_format(self):
        location = "Taman Negara Kuala Tahan, Jerantut, Pahang"
        result = scraper.extract_state_from_location(location)
        assert result == "Pahang"
    
    def test_extract_state_city_only(self):
        location = "Kuala Lumpur"
        result = scraper.extract_state_from_location(location)
        assert result == ""  # Single word, no state
    
    def test_extract_state_known_city_state(self):
        location = "KLCC, Kuala Lumpur"
        result = scraper.extract_state_from_location(location)
        assert result == "Kuala Lumpur"
    
    def test_extract_state_empty_location(self):
        result = scraper.extract_state_from_location("")
        assert result == ""


class TestDistanceExtraction:
    """Tests for extract_distance_from_name function"""
    
    def test_extract_distance_half_marathon(self):
        name = "Kota Belud Half Marathon"
        result = scraper.extract_distance_from_name(name)
        assert result == "21km"
    
    def test_extract_distance_hm_abbreviation(self):
        name = "Penang HM 2026"
        result = scraper.extract_distance_from_name(name)
        assert result == "21km"
    
    def test_extract_distance_marathon(self):
        name = "Kuala Lumpur Marathon"
        result = scraper.extract_distance_from_name(name)
        assert result == "42km"
    
    def test_extract_distance_42km(self):
        name = "Standard Chartered Marathon - 42KM"
        result = scraper.extract_distance_from_name(name)
        assert result == "42km"
    
    def test_extract_distance_ultra(self):
        name = "Malaysia Taman Negara Ultra"
        result = scraper.extract_distance_from_name(name)
        assert result == "50km+"
    
    def test_extract_distance_5k(self):
        name = "5K Malaysia Speed"
        result = scraper.extract_distance_from_name(name)
        assert result == "5km"
    
    def test_extract_distance_10km(self):
        name = "City Run 10KM"
        result = scraper.extract_distance_from_name(name)
        assert result == "10km"
    
    def test_extract_distance_not_found(self):
        name = "Trail Run Adventure"
        result = scraper.extract_distance_from_name(name)
        assert result == ""


class TestURLValidation:
    """Tests for validate_url function"""
    
    def test_validate_url_https(self):
        assert scraper.validate_url("https://example.com") is True
    
    def test_validate_url_http(self):
        assert scraper.validate_url("http://example.com") is True
    
    def test_validate_url_invalid(self):
        assert scraper.validate_url("not-a-url") is False
    
    def test_validate_url_empty(self):
        assert scraper.validate_url("") is False


class TestDateValidation:
    """Tests for validate_date function"""
    
    def test_validate_date_valid_current_year(self):
        current_year = datetime.now().year
        date_str = f"{current_year}-06-15"
        assert scraper.validate_date(date_str) is True
    
    def test_validate_date_valid_future_year(self):
        future_year = datetime.now().year + 1
        date_str = f"{future_year}-06-15"
        assert scraper.validate_date(date_str) is True
    
    def test_validate_date_past_year(self):
        past_year = datetime.now().year - 1
        date_str = f"{past_year}-06-15"
        assert scraper.validate_date(date_str) is False
    
    def test_validate_date_invalid_format(self):
        assert scraper.validate_date("2026/06/15") is False
    
    def test_validate_date_invalid_month(self):
        assert scraper.validate_date("2026-13-15") is False
    
    def test_validate_date_invalid_day(self):
        assert scraper.validate_date("2026-06-32") is False
    
    def test_validate_date_empty(self):
        assert scraper.validate_date("") is False


class TestEventValidation:
    """Tests for validate_event function"""
    
    def test_validate_event_valid(self, sample_event):
        is_valid, errors = scraper.validate_event(sample_event)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_event_missing_name(self, sample_event):
        sample_event['name'] = ""
        is_valid, errors = scraper.validate_event(sample_event)
        assert is_valid is False
        assert any("Name" in error for error in errors)
    
    def test_validate_event_short_name(self, sample_event):
        sample_event['name'] = "AB"
        is_valid, errors = scraper.validate_event(sample_event)
        assert is_valid is False
        assert any("Name" in error for error in errors)
    
    def test_validate_event_missing_date(self, sample_event):
        sample_event['date'] = ""
        is_valid, errors = scraper.validate_event(sample_event)
        assert is_valid is False
        assert any("Date" in error for error in errors)
    
    def test_validate_event_invalid_date(self, sample_event):
        sample_event['date'] = "2020-01-01"  # Past date
        is_valid, errors = scraper.validate_event(sample_event)
        assert is_valid is False
        assert any("date" in error.lower() for error in errors)
    
    def test_validate_event_missing_url(self, sample_event):
        sample_event['registration_url'] = ""
        is_valid, errors = scraper.validate_event(sample_event)
        assert is_valid is False
        assert any("URL" in error for error in errors)
    
    def test_validate_event_invalid_url(self, sample_event):
        sample_event['registration_url'] = "not-a-url"
        is_valid, errors = scraper.validate_event(sample_event)
        assert is_valid is False
        assert any("URL" in error for error in errors)


class TestDatasetValidation:
    """Tests for validate_dataset function"""
    
    def test_validate_dataset_basic_stats(self, sample_events_list):
        report = scraper.validate_dataset(sample_events_list)
        
        assert report['total_events'] == 3
        assert report['valid_events'] == 3
        assert report['invalid_events'] == 0
        assert report['stats']['with_names'] == 3
        assert report['stats']['with_urls'] == 3
    
    def test_validate_dataset_extraction_rates(self, sample_events_list):
        report = scraper.validate_dataset(sample_events_list)
        
        assert report['stats']['state_extraction_rate'] == 100.0
        assert report['stats']['distance_extraction_rate'] == 100.0
    
    def test_validate_dataset_distributions(self, sample_events_list):
        report = scraper.validate_dataset(sample_events_list)
        
        assert 'states' in report['distributions']
        assert 'distances' in report['distributions']
        assert report['distributions']['states']['Kuala Lumpur'] == 2
        assert report['distributions']['distances']['21km'] == 1
    
    def test_validate_dataset_empty(self):
        report = scraper.validate_dataset([])
        assert report['total_events'] == 0
        assert 'error' in report['stats']
    
    def test_validate_dataset_duplicates(self, sample_events_list):
        # Add a duplicate
        sample_events_list.append(sample_events_list[0].copy())
        report = scraper.validate_dataset(sample_events_list)
        
        assert report['duplicates'] == 1


class TestIntegration:
    """Integration tests for the full scraping workflow"""
    
    def test_scrape_mock_html(self, mock_html_full_page):
        """Test scraping with mock HTML"""
        events = scraper.scrape_event_data(mock_html_full_page)
        
        assert len(events) == 4
        assert all(e.get('name') for e in events)
        assert all(e.get('date') for e in events)
        assert all(e.get('registration_url') for e in events)
    
    def test_scrape_extracts_state_and_distance(self, mock_html_full_page):
        """Test that state and distance are extracted"""
        events = scraper.scrape_event_data(mock_html_full_page)
        
        # Check that at least some events have state and distance
        states = [e.get('state') for e in events if e.get('state')]
        distances = [e.get('distance') for e in events if e.get('distance')]
        
        assert len(states) > 0
        assert len(distances) > 0
