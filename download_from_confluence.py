import requests
import os
from urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urljoin
from dotenv import load_dotenv

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Load environment variables from .env file
load_dotenv()

# CONNECTION INFO - Now from environment variables
CONFLUENCE_URL = os.getenv('CONFLUENCE_URL', 'https://confluence.example.com')
USERNAME = os.getenv('CONFLUENCE_USERNAME', 'admin')
PASSWORD = os.getenv('CONFLUENCE_PASSWORD', 'password')
SPACE_KEY = os.getenv('CONFLUENCE_SPACE_KEY', 'TEST')
PARENT_PAGE_TITLE = os.getenv('CONFLUENCE_PARENT_PAGE_TITLE', 'Root Page')
OUTPUT_DIR = os.getenv('CONFLUENCE_OUTPUT_DIR', './pdfs')
ATTACHMENTS_DIR = os.getenv('CONFLUENCE_ATTACHMENTS_DIR', './attachments')
VERIFY_SSL = os.getenv('CONFLUENCE_VERIFY_SSL', 'true').lower() == 'true'

def get_parent_page_id(page_title):
    response = requests.get(
        f"{CONFLUENCE_URL}/rest/api/content",
        auth=(USERNAME, PASSWORD),
        params={
            "spaceKey": SPACE_KEY,
            "title": page_title,
            "expand": "ancestors"
        }
    )

    if response.status_code == 200:
        data = response.json()
        if data["results"]:
            parent_page_id = data["results"][0]["id"]
            print(f"Parent Page ID: {parent_page_id}")
            return(parent_page_id)
        else:
            print("Page not found")
            return None
    else:
        print(f"Error: {response.status_code}")
        return None





def get_children_recursive(parent_id):
    """Recursively fetch all child pages under a parent"""
    all_pages = []
    start = 0
    limit = 100  # Confluence's max per request

    while True:
        url = urljoin(CONFLUENCE_URL, f"/rest/api/content/{parent_id}/child/page")
        params = {
            "limit": limit,
            "start": start,
            "expand": "children.page"
        }

        response = requests.get(
            url,
            auth=(USERNAME, PASSWORD),
            params=params,
            verify=VERIFY_SSL
        )

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break

        data = response.json()
        children = data["results"]
        all_pages.extend(children)

        # Recursively fetch grandchildren
        for child in children:
            all_pages.extend(get_children_recursive(child["id"]))

        if data["size"] < limit:
            break

        start += limit

    return all_pages

def export_pdf_and_attachments(page_id, title):
    safe_title = "".join(c if c.isalnum() or c == '_' else '_' for c in title).rstrip('_')

    # Export PDF
    pdf_url = urljoin(CONFLUENCE_URL, f"/spaces/flyingpdf/pdfpageexport.action?pageId={page_id}")
    pdf_response = requests.get(pdf_url, auth=(USERNAME, PASSWORD), stream=True, verify=VERIFY_SSL)

    if pdf_response.status_code == 200:
        with open(f"{OUTPUT_DIR}/{safe_title}.pdf", "wb") as f:
            for chunk in pdf_response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Exported PDF: {safe_title}.pdf")
    else:
        print(f"Failed to export PDF {title}: {pdf_response.status_code}")

    # Get attachments using proper API endpoint
    attachments_url = urljoin(CONFLUENCE_URL, f"/rest/api/content/{page_id}/child/attachment")
    attachments_response = requests.get(attachments_url, auth=(USERNAME, PASSWORD), verify=VERIFY_SSL)

    if attachments_response.status_code == 200:
        attachments = attachments_response.json()["results"]
        for attachment in attachments:
            # Use the download link from the attachment metadata
            download_url = urljoin(CONFLUENCE_URL, attachment["_links"]["download"])

            attachment_response = requests.get(download_url, auth=(USERNAME, PASSWORD), stream=True, verify=VERIFY_SSL)
            if attachment_response.status_code == 200:
                attachment_filename = f"{safe_title}_{attachment['title']}"
                with open(f"{ATTACHMENTS_DIR}/{attachment_filename}", "wb") as f:
                    for chunk in attachment_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Downloaded attachment: {attachment_filename}")
            else:
                print(f"Failed to download attachment: {download_url} - {attachment_response.status_code}")
    else:
        print(f"Failed to fetch attachments for {title}: {attachments_response.status_code}")

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
    print("Fetching all child pages recursively...")
    parent_page_id = get_parent_page_id(PARENT_PAGE_TITLE)
    if not parent_page_id:
        print(f"Could not find parent page: {PARENT_PAGE_TITLE}")
        exit(1)
    
    all_pages = get_children_recursive(parent_page_id)
    print(f"Found {len(all_pages)} pages. Starting export...")

    for page in all_pages:
        export_pdf_and_attachments(page["id"], page["title"])
