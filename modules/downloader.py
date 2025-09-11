import requests
import os
from urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urljoin
from typing import List, Dict, Any, Optional
import urllib3

# Suppress SSL warnings (same as original)
urllib3.disable_warnings(category=InsecureRequestWarning)


class ConfluenceDownloader:
    """Simple refactoring of the original download_from_confluence.py functions"""

    def __init__(
        self,
        confluence_url: str,
        username: str,
        password: str,
        space_key: str,
        output_dir: str,
        attachments_dir: Optional[str] = None,
        verify_ssl: bool = True,
    ) -> None:
        self.confluence_url = confluence_url
        self.username = username
        self.password = password
        self.space_key = space_key
        self.output_dir = output_dir
        # If no separate attachments directory is provided, use output_dir for backward compatibility
        self.attachments_dir = attachments_dir or output_dir
        self.verify_ssl = verify_ssl

    def get_parent_page_id(self, page_title: str) -> Optional[str]:
        """Exact copy of the original get_parent_page_id function"""
        response = requests.get(
            f"{self.confluence_url}/rest/api/content",
            auth=(self.username, self.password),
            params={"spaceKey": self.space_key, "title": page_title, "expand": "ancestors"},
            verify=self.verify_ssl,
        )

        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                parent_page_id = data["results"][0]["id"]
                print(f"Parent Page ID: {parent_page_id}")
                return parent_page_id
            else:
                print("Page not found")
                return None
        else:
            print(f"Error: {response.status_code}")
            return None

    def get_children_recursive(self, parent_id: str) -> List[Dict[str, Any]]:
        """Exact copy of the original get_children_recursive function"""
        all_pages: List[Dict[str, Any]] = []
        start = 0
        limit = 100  # Confluence's max per request

        while True:
            url = urljoin(self.confluence_url, f"/rest/api/content/{parent_id}/child/page")
            params = {"limit": limit, "start": start, "expand": "children.page"}

            response = requests.get(  # type: ignore[arg-type]
                url, auth=(self.username, self.password), params=params, verify=self.verify_ssl
            )

            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                break

            data = response.json()
            children = data["results"]
            all_pages.extend(children)

            # Recursively fetch grandchildren
            for child in children:
                all_pages.extend(self.get_children_recursive(child["id"]))

            if data["size"] < limit:
                break

            start += limit

        return all_pages

    def export_pdf_and_attachments(self, page_id: str, title: str) -> None:
        """Exact copy of the original export_pdf_and_attachments function"""
        safe_title = "".join(c if c.isalnum() or c == "_" else "_" for c in title).rstrip("_")

        # Export PDF
        pdf_url = urljoin(self.confluence_url, f"/spaces/flyingpdf/pdfpageexport.action?pageId={page_id}")
        pdf_response = requests.get(pdf_url, auth=(self.username, self.password), stream=True, verify=self.verify_ssl)

        if pdf_response.status_code == 200:
            with open(f"{self.output_dir}/{safe_title}.pdf", "wb") as f:
                for chunk in pdf_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Exported PDF: {safe_title}.pdf")
        else:
            print(f"Failed to export PDF {title}: {pdf_response.status_code}")

        # Get attachments using proper API endpoint
        attachments_url = urljoin(self.confluence_url, f"/rest/api/content/{page_id}/child/attachment")
        attachments_response = requests.get(
            attachments_url, auth=(self.username, self.password), verify=self.verify_ssl
        )

        if attachments_response.status_code == 200:
            attachments = attachments_response.json()["results"]
            for attachment in attachments:
                # Use the download link from the attachment metadata
                download_url = urljoin(self.confluence_url, attachment["_links"]["download"])

                attachment_response = requests.get(
                    download_url, auth=(self.username, self.password), stream=True, verify=self.verify_ssl
                )
                if attachment_response.status_code == 200:
                    attachment_filename = f"{safe_title}_{attachment['title']}"
                    with open(f"{self.attachments_dir}/{attachment_filename}", "wb") as f:
                        for chunk in attachment_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Downloaded attachment: {attachment_filename}")
                else:
                    print(f"Failed to download attachment: {download_url} - {attachment_response.status_code}")
        else:
            print(f"Failed to fetch attachments for {title}: {attachments_response.status_code}")

    def run(self, parent_page_title: str) -> bool:
        """Main execution logic from the original __main__ block"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.attachments_dir, exist_ok=True)
        print("Fetching parent page ID...")
        parent_page_id = self.get_parent_page_id(parent_page_title)
        if not parent_page_id:
            print(f"Could not find parent page: {parent_page_title}")
            return False

        print("Fetching all child pages recursively...")
        all_pages = self.get_children_recursive(parent_page_id)
        print(f"Found {len(all_pages)} pages. Starting export...")

        for page in all_pages:
            self.export_pdf_and_attachments(page["id"], page["title"])

        return True
