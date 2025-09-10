#!/usr/bin/env python3
"""
New entry point using the refactored ConfluenceDownloader class.
This should behave identically to the original download_from_confluence.py
"""

import os
from dotenv import load_dotenv
from modules.downloader import ConfluenceDownloader

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
CONFLUENCE_URL = os.getenv('CONFLUENCE_URL', 'https://confluence.example.com')
USERNAME = os.getenv('CONFLUENCE_USERNAME', 'admin')
PASSWORD = os.getenv('CONFLUENCE_PASSWORD', 'password')
SPACE_KEY = os.getenv('CONFLUENCE_SPACE_KEY', 'TEST')
PARENT_PAGE_TITLE = os.getenv('CONFLUENCE_PARENT_PAGE_TITLE', 'Root Page')
OUTPUT_DIR = os.getenv('CONFLUENCE_OUTPUT_DIR', './output/pdfs')
VERIFY_SSL = os.getenv('CONFLUENCE_VERIFY_SSL', 'true').lower() == 'true'

if __name__ == "__main__":
    # Create downloader with same configuration
    downloader = ConfluenceDownloader(
        confluence_url=CONFLUENCE_URL,
        username=USERNAME,
        password=PASSWORD,
        space_key=SPACE_KEY,
        output_dir=OUTPUT_DIR,
        verify_ssl=VERIFY_SSL
    )
    
    # Run with same behavior as original
    success = downloader.run(PARENT_PAGE_TITLE)
    if not success:
        exit(1)
