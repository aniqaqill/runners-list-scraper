"""
Main entry point for the scraper.

Usage:
    python -m src.main [options]
    
Options:
    --url URL       Override the default scraping URL
    --output DIR    Output directory for JSON/CSV files
    --no-api        Skip API sync even if credentials are set
"""
import argparse
import sys
from pathlib import Path

from src.config import (
    get_logger,
    get_api_url,
    get_api_key,
    get_scrape_url,
    is_api_configured,
    DEFAULT_JSON_OUTPUT,
    DEFAULT_CSV_OUTPUT,
)
from src.services.browser import fetch_page
from src.services.parser import scrape_event_data
from src.services.api_client import send_to_api, APIError, AuthenticationError
from src.services.file_exporter import save_to_json, save_to_csv
from src.utils.validators import validate_dataset, print_validation_report

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape running events and sync to API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
    API_URL     URL of the internal sync endpoint
    API_KEY     API key for authentication
    SCRAPE_URL  Override the default scraping URL

Examples:
    python -m src.main
    python -m src.main --url https://example.com/events.html
    python -m src.main --output ./data --no-api
        """
    )
    
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Override the default scraping URL"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=".",
        help="Output directory for JSON/CSV files (default: current directory)"
    )
    
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Skip API sync even if credentials are configured"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main() -> int:
    """Main execution function.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    args = parse_args()
    
    # Set up verbose logging if requested
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Determine URL to scrape
        url = args.url or get_scrape_url()
        
        if not url:
            print("\n Error: SCRAPE_URL environment variable is not set.")
            print("   Set it in .env file or use --url argument.")
            print("   Example: SCRAPE_URL=https://pm1.blogspot.com/p/running-event-2026.html")
            return 1
        
        # Fetch and parse the page
        print(f"\n📡 Fetching events from: {url}")
        soup = fetch_page(url)
        
        # Extract event data
        print("🔍 Extracting event data...")
        events = scrape_event_data(soup)
        
        if not events:
            logger.warning("No events were extracted! Check the HTML structure.")
            print("\n⚠ No events were extracted. Check the logs for details.")
            return 1
        
        # Validate dataset
        print("Validating events...")
        validation_report = validate_dataset(events)
        
        # Set up output paths
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        json_path = output_dir / DEFAULT_JSON_OUTPUT
        csv_path = output_dir / DEFAULT_CSV_OUTPUT
        
        # Save the data locally
        save_to_json(events, str(json_path))
        save_to_csv(events, str(csv_path))
        
        print(f"\n✓ Scraping completed")
        print(f"Total events extracted: {len(events)}")
        print(f"Data saved to {json_path} and {csv_path}")
        
        # Print validation report
        print_validation_report(validation_report)
        
        # Send to API if configured and not disabled
        if args.no_api:
            print("API sync skipped (--no-api flag)")
        elif is_api_configured():
            api_url = get_api_url()
            api_key = get_api_key()
            
            print("Syncing to API...")
            try:
                result = send_to_api(events, api_url, api_key)
                print(f"✓ Successfully synced {result.get('total', 0)} events to API")
                print(f"  - Inserted: {result.get('inserted', 0)}")
                print(f"  - Updated: {result.get('updated', 0)}")
            except AuthenticationError as e:
                logger.error(f"API authentication failed: {e}")
                print(f"API authentication failed: {e}")
                print("Data was saved locally.")
                return 1
            except APIError as e:
                logger.error(f"Failed to sync to API: {e}")
                print(f"Failed to sync to API: {e}")
                print("Data was saved locally.")
        else:
            logger.info("API_URL or API_KEY not set, skipping API sync")
            print("API sync skipped (API_URL and API_KEY not set)")
        
        return 0
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        return 130
        
    except Exception as e:
        logger.exception(f"Scraping failed: {e}")
        print(f"\nScraping failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
