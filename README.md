# Runners List Scraper

A Python web scraper for extracting running event data from Blogger pages, with comprehensive validation and Go API schema alignment.

## Features

- **Schema Aligned** - Matches Go API Event struct with state and distance fields
- **Smart Extraction** - Automatically extracts state from location and distance from event name
- **Comprehensive Validation** - URL, date, event, and dataset validation with detailed reporting
- **Sustainable** - Dynamic year validation (no code changes needed annually)
- **Well Tested** - 48 unit and integration tests with 62% code coverage
- **Production Ready** - Detailed logging, error handling, and quality reports

## Installation

```bash
# Clone the repository
git clone https://github.com/aniqaqill/runners-list-scraper.git
cd runners-list-scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run the Scraper

```bash
python scraper.py
```

### Output

The scraper generates three files:

1. **`events.json`** - JSON array of events
2. **`events.csv`** - CSV export for analysis
3. **Validation Report** - Printed to console

### Sample Output

```json
{
  "name": "Kota Belud Half Marathon",
  "location": "Kota Belud, Sabah",
  "state": "Sabah",
  "distance": "21km",
  "date": "2026-11-08",
  "description": "",
  "registration_url": "https://checkpointspot.asia/event/..."
}
```

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run with Coverage

```bash
pytest tests/ --cov=scraper --cov-report=html
```

View coverage report: `open htmlcov/index.html`

### Test Statistics

- **Total Tests**: 48
- **Pass Rate**: 100%
- **Code Coverage**: 62%

## Data Schema

### Event Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Event name |
| `location` | string | maybe | Full location string |
| `state` | string | no | Malaysian state (extracted) |
| `distance` | string | no | Race distance (extracted) |
| `date` | string | yes | YYYY-MM-DD format |
| `description` | string | no | Currently empty |
| `registration_url` | string | yes | Event registration link |

### Extraction Rates

- **State**: ~70% (from location string)
- **Distance**: ~37% (from event name)

## Validation

### Event Validation

- Name: Non-empty, minimum 3 characters
- Date: YYYY-MM-DD format, current year or future
- URL: Valid HTTP/HTTPS format
- Location: Optional but logged if missing
- State: Optional, extracted from location
- Distance: Optional, extracted from name

### Dataset Validation

Automatic checks for:
- Duplicate events (same name + date)
- Month coverage (minimum 6 months)
- Extraction rates (state >80%, distance >60%)
- Data completeness

## Project Structure

```
runners-list-scraper/
├── scraper.py              # Main scraper with validation
├── requirements.txt        # Python dependencies
├── pytest.ini             # Pytest configuration
├── .gitignore
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # Pytest fixtures
│   └── test_scraper.py    # Test suite (48 tests)
├── events.json            # Output (gitignored)
├── events.csv             # Output (gitignored)
└── htmlcov/               # Coverage report (gitignored)
```

## Development

### Adding New Tests

1. Add test fixtures to `tests/conftest.py`
2. Add test functions to `tests/test_scraper.py`
3. Run tests: `pytest tests/ -v`

### Improving Extraction Rates

**State Extraction:**
- Add more Malaysian state variations
- Handle edge cases in location parsing

**Distance Extraction:**
- Add more distance patterns to `DISTANCE_PATTERNS`
- Handle multi-distance events better

## Future Enhancements

- [ ] API integration (POST to Go backend)
- [ ] GitHub Actions for daily scraping
- [ ] Improved distance extraction patterns
- [ ] State normalization for city-states

## License

MIT

## Author

Aniq Aqil (@aniqaqill)
