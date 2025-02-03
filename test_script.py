import pytest
import json
import sys
import time
from unittest.mock import patch, MagicMock
from mapigator import fetch_places, scrape_reviews, display_places
from rich.console import Console
from io import StringIO


@pytest.fixture
def mock_places_response():
    return {
        "results": [
            {
                "name": "Test Hospital",
                "rating": 4.5,
                "place_id": "test123",
                "geometry": {"location": {"lat": 40.7128, "lng": -74.0060}}
            }
        ],
        "status": "OK"
    }

@patch("requests.get")
def test_fetch_places(mock_get, mock_places_response):
    mock_get.return_value.json.return_value = mock_places_response
    places = fetch_places(40.7128, -74.0060, 1000, "hospital", verbose=False)
    
    assert len(places) == 1
    assert places[0]["name"] == "Test Hospital"
    assert places[0]["rating"] == 4.5
    assert places[0]["place_id"] == "test123"
    assert places[0]["geometry"]["location"]["lat"] == 40.7128
    assert places[0]["geometry"]["location"]["lng"] == -74.0060


@patch("selenium.webdriver.Chrome")
def test_scrape_reviews(mock_chrome):
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    
    mock_review_element = MagicMock()
    mock_review_element.find_element.return_value.text = "Great place!"
    mock_review_element.find_elements.return_value = [MagicMock()] * 5
    
    mock_driver.find_element.return_value = MagicMock()
    mock_driver.find_elements.return_value = [mock_review_element]
    
    reviews = scrape_reviews("test123")
    
    assert len(reviews) > 0
    assert reviews[0]["text"] == "Great place!"


@patch("sys.stdout", new_callable=StringIO)
def test_display_places(mock_stdout):
    console = Console(file=mock_stdout)
    places = [{
        "name": "Test Hospital",
        "rating": 4.5,
        "place_id": "test123",
        "geometry": {"location": {"lat": 40.7128, "lng": -74.0060}}
    }]
    
    display_places(places)
    output = mock_stdout.getvalue()
    assert "Test Hospital" in output
    assert "4.5" in output
    assert "test123" in output
    assert "40.7128" in output
    assert "-74.0060" in output


if __name__ == "__main__":
    pytest.main()
