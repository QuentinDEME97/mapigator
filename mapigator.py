import argparse
import time
import logging
import sys
import requests
import os
from dotenv import load_dotenv
import json
from rich.syntax import Syntax
from rich.console import Console
from rich.table import Table
from rich.progress import SpinnerColumn, Progress
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
console = Console()

# Load environment variables
load_dotenv()

# Google API Configuration
API_KEY = os.getenv("API_KEY")
PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

if not API_KEY:
    print("❌ ERROR: API_KEY is missing. Please set it in the .env file.")
    sys.exit(1)

# Chrome WebDriver path (modify if needed)
CHROME_DRIVER_PATH = "./chromedriver"


def fetch_places(lat, lng, radius, types, verbose):
    """Fetch places using Google Places API."""
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "key": API_KEY
    }

    if types:
        formatted_types = "|".join(types.split(","))
        params["type"] = formatted_types

    places = []
    next_page_token = None

    with Progress(SpinnerColumn(), console=console) as progress:
        task = progress.add_task("[cyan]Fetching places...", total=None)

        while True:
            if next_page_token:
                params["pagetoken"] = next_page_token

            response = requests.get(PLACES_URL, params=params)
            data = response.json()

            if verbose:
                console.print("[bold green]Raw API Response:[/bold green]")
                pretty_json = json.dumps(data, indent=2)
                console.print(Syntax(pretty_json, "json", theme="monokai", word_wrap=True))

            if "results" in data:
                places.extend(data["results"])
            else:
                logging.error("Error fetching places: %s", data)
                break

            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break

            time.sleep(2)  # Google API requires a delay before using next_page_token

        progress.remove_task(task)

    return places


def scrape_reviews(place_id):
    """Scrape reviews for a place using Selenium."""

    # Google Maps place URL
    url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

    # Set up Selenium WebDriver with headless mode
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    console.print(f"[bold cyan]Opening Google Maps for place ID: {place_id}...[/bold cyan]")
    driver.get(url)
    time.sleep(5)

    try:
        # Find and click the "See all reviews" button
        review_button = driver.find_element(By.XPATH, "//button[contains(text(), 'reviews')]")
        review_button.click()
        time.sleep(3)

        # Scroll to load more reviews
        console.print("[bold yellow]Loading all reviews...[/bold yellow]")
        scrollable_div = driver.find_element(By.CLASS_NAME, "m6QErb")

        for _ in range(10):  # Scroll 10 times (adjust if needed)
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            time.sleep(1)

        # Extract reviews
        reviews = []
        review_elements = driver.find_elements(By.CLASS_NAME, "jftiEf")

        for review in review_elements:
            author = review.find_element(By.CLASS_NAME, "d4r55").text
            rating = len(review.find_elements(By.CLASS_NAME, "kvMYJc"))
            text = review.find_element(By.CLASS_NAME, "wiI7pd").text

            reviews.append({
                "author": author,
                "rating": rating,
                "text": text
            })

        console.print(f"[bold green]Scraped {len(reviews)} reviews![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error scraping reviews: {e}[/bold red]")
        reviews = []

    driver.quit()
    return reviews


def display_places(places):
    """Display places in a table format with coordinates."""
    table = Table(title="Places Found")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Rating", style="magenta")
    table.add_column("Place ID", style="green")
    table.add_column("Latitude", style="blue")
    table.add_column("Longitude", style="blue")

    for place in places:
        location = place.get("geometry", {}).get("location", {})
        lat = str(location.get("lat", "N/A"))
        lng = str(location.get("lng", "N/A"))

        table.add_row(
            place.get("name", "N/A"),
            str(place.get("rating", "N/A")),
            place["place_id"],
            lat,
            lng
        )

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Fetch and scrape Google Reviews for places in a given area.")
    parser.add_argument("lat", type=float, help="Latitude of the location")
    parser.add_argument("lng", type=float, help="Longitude of the location")
    parser.add_argument("radius", type=int, help="Radius in meters (max 50000)")
    parser.add_argument("-t", "--types", type=str, help="Filter places by types (comma-separated, e.g., 'hospital,pharmacy,doctor')")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation and scrape reviews immediately")
    parser.add_argument("-v", "--verbose", action="store_true", help="Display raw API response in JSON format")

    args = parser.parse_args()

    # Fetch places
    places = fetch_places(args.lat, args.lng, args.radius, args.types, args.verbose)

    if not places:
        console.print("[bold red]No places found.[/bold red]")
        sys.exit(1)

    console.print(f"[bold green]Found {len(places)} places.[/bold green]")
    display_places(places)

    # Ask for confirmation
    if not args.yes:
        confirm = input("Do you want to scrape reviews for these places? (y/N): ").strip().lower()
        if confirm != "y":
            console.print("[bold yellow]Exiting without scraping.[/bold yellow]")
            sys.exit(0)

    # Scrape reviews
    console.print("[bold cyan]Scraping reviews...[/bold cyan]")

    for place in places:
        place_name = place.get("name", "Unknown Place")
        place_id = place["place_id"]

        console.print(f"\n[bold]Fetching reviews for {place_name}...[/bold]")
        reviews = scrape_reviews(place_id)

        for review in reviews:
            console.print(f"⭐ {review['rating']} - {review['author']}: {review['text']}")

    console.print("[bold green]Done![/bold green]")


if __name__ == "__main__":
    main()
