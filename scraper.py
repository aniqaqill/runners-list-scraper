from bs4 import BeautifulSoup
import json
import csv
from urllib.parse import urljoin
from selenium import webdriver
import time

# Set up Selenium WebDriver
driver = webdriver.Chrome()  # Ensure you have ChromeDriver installed
driver.get("https://pm1.blogspot.com/p/2024-event-calendar.html")

# Wait for the page to load
time.sleep(5)

# Get the page source and parse it with BeautifulSoup
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

def scrape_event_data(soup):
    events = []  # Use a list to store events

    # Month mapping for date parsing
    months = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
        "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
        "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
    }

    # Loop through all <h4> tags for months/years
    for header in soup.find_all('h4'):
        month_year = header.text.strip()  # Example: "JANUARY 2025"
        
        # If the text matches a month-year pattern, extract month and year
        if len(month_year.split()) == 2:
            try:
                month_name, year = month_year.split()
                current_year = int(year)
            except ValueError:
                continue

            # Look for event entries (in sibling <ul> tags)
            next_sibling = header.find_next_sibling('ul')
            while next_sibling:
                for li in next_sibling.find_all('li'):
                    text = li.text.strip()
                    link = li.find('a')  # Find the link if available
                    
                    if " - " in text:
                        try:
                            # Split the event text into date and details
                            split_idx = text.index(" - ")
                            date = text[:split_idx].strip()
                            details = text[split_idx + 3:].strip()
                            
                            # Ensure the date contains valid day and month
                            date_parts = date.split()
                            if len(date_parts) < 2:
                                continue
                            
                            day = date_parts[0]
                            month_abbr = date_parts[1]
                            month_num = months.get(month_abbr[:3], "00")
                            full_date = f"{current_year}-{month_num}-{day.zfill(2)}"
                            
                            # Extract event name and location
                            if "(" in details and ")" in details:
                                name, location = details.split("(", 1)
                                location = location.replace(")", "").strip()
                            else:
                                name = details
                                location = ""
                            
                            # Registration URL from the hyperlink
                            registration_url = link['href'] if link else ""

                            # Append the event data
                            events.append({
                                "name": name.strip(),
                                "location": location,
                                "date": full_date,
                                "description": "",
                                "registration_url": registration_url
                            })
                        except ValueError:
                            continue

                # Move to the next sibling
                next_sibling = next_sibling.find_next_sibling('ul')

    return events

def save_to_json(events, filename="events.json"):
    with open(filename, "w") as f:
        json.dump(events, f, indent=4)

def save_to_csv(events, filename="events.csv"):
    keys = ["name", "location", "date", "description", "registration_url"]
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(events)

# Main execution
event_data = scrape_event_data(soup)

# Save the data
save_to_json(event_data)
save_to_csv(event_data)

print("Scraping completed. Data saved to events.json and events.csv.")