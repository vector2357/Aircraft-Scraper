import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Adiciona o src ao path do Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.web_scraping import FirecrawlScraper

@pytest.fixture
def mock_firecrawl_app():
    """Mock da FirecrawlApp"""
    with patch('src.web_scraping.FirecrawlApp') as mock_app:
        mock_instance = MagicMock()
        mock_app.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def scraper(mock_firecrawl_app):
    """Fixture do scraper com mock"""
    return FirecrawlScraper(api_key="test_key")

@pytest.fixture
def sample_html_content():
    """HTML de exemplo para testes"""
    return """
    <html>
        <head><title>Test Aircraft Listing</title></head>
        <body>
            <h1>Piper PA-28-181 Archer LX</h1>
            <div class="price">USD $150,000</div>
            <div class="location">Orlando, FL</div>
            <p>Total Time: 2500 hours</p>
            <p>Engine 1 Time: 1500 hours</p>
            <p>Engine 1 TBO: 2000 hours</p>
            <div class="seller">Aircraft Sales Inc.</div>
            <div class="phone">(123) 456-7890</div>
            <p>This is a beautiful aircraft with many upgrades and recent maintenance.</p>
        </body>
    </html>
    """

@pytest.fixture
def sample_search_html():
    """HTML de página de busca com links"""
    return """
    <html>
        <head><title>Aircraft Search Results</title></head>
        <body>
            <a href="/listing/piper-archer-123" class="list-listing-title-link">Piper Archer</a>
            <a href="/listing/cessna-172-456" class="list-listing-title-link">Cessna 172</a>
            <a href="/about">About Us</a>
            <a href="/contact">Contact</a>
        </body>
    </html>
    """

@pytest.fixture
def sample_urls():
    """URLs de exemplo para testes"""
    return {
        'search_url': "https://www.controller.com/listings/search?Manufacturer=PIPER",
        'listing_url': "https://www.controller.com/listing/piper-archer-123",
        'invalid_url': "https://invalid-url.com"
    }