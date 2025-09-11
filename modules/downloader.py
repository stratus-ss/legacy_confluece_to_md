import requests
import os
import logging
from urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urljoin
from typing import List, Dict, Any, Optional, Tuple
import urllib3

# Suppress SSL warnings (same as original)
urllib3.disable_warnings(category=InsecureRequestWarning)

logger = logging.getLogger(__name__)


class ConfluenceDownloader:
    """Confluence downloader with comprehensive metadata tracking and statistics"""

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
        """Initialize the Confluence downloader

        Args:
            confluence_url: Base URL of the Confluence instance
            username: Confluence username
            password: Confluence password/API token
            space_key: Confluence space key to download from
            output_dir: Directory for PDF exports
            attachments_dir: Directory for attachments (defaults to output_dir)
            verify_ssl: Whether to verify SSL certificates
        """
        self.confluence_url = confluence_url
        self.username = username
        self.password = password
        self.space_key = space_key
        self.output_dir = output_dir
        # If no separate attachments directory is provided, use output_dir for backward compatibility
        self.attachments_dir = attachments_dir or output_dir
        self.verify_ssl = verify_ssl

        # Metadata tracking (always enabled)
        self.page_metadata: Dict[str, Dict] = {}  # page_id -> metadata
        self.attachment_metadata: Dict[str, List[Dict]] = {}  # page_id -> attachments
        self.downloaded_attachments: Dict[str, List[str]] = {}  # page_title -> filenames

        logger.info("Confluence downloader initialized with comprehensive tracking")

    def get_parent_page_id(self, page_title: str) -> Optional[str]:
        """Get the parent page ID from Confluence by title"""
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
                logger.info(f"Parent Page ID: {parent_page_id}")
                return parent_page_id
            else:
                logger.warning("Page not found")
                return None
        else:
            logger.error(f"Error fetching parent page: {response.status_code}")
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

    def export_pdf_and_attachments(self, page_id: str, title: str) -> Tuple[bool, Dict[str, Any]]:
        """Export PDF and attachments with comprehensive metadata tracking

        Args:
            page_id: Confluence page ID
            title: Page title

        Returns:
            Tuple of (success, metadata_dict)
        """
        safe_title = "".join(c if c.isalnum() or c == "_" else "_" for c in title).rstrip("_")

        # Initialize result tracking
        result: Dict[str, Any] = {
            "page_id": page_id,
            "title": title,
            "safe_title": safe_title,
            "pdf_exported": False,
            "attachments_downloaded": 0,
            "attachments_failed": 0,
            "attachment_files": [],
            "images_count": 0,
            "errors": [],
        }

        # Store page metadata
        self.page_metadata[page_id] = {"title": title, "safe_title": safe_title, "id": page_id}

        try:
            # Export PDF
            pdf_url = urljoin(self.confluence_url, f"/spaces/flyingpdf/pdfpageexport.action?pageId={page_id}")
            pdf_response = requests.get(
                pdf_url, auth=(self.username, self.password), stream=True, verify=self.verify_ssl
            )

            if pdf_response.status_code == 200:
                pdf_file_path = f"{self.output_dir}/{safe_title}.pdf"
                with open(pdf_file_path, "wb") as f:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
                        f.write(chunk)

                result["pdf_exported"] = True
                logger.info(f"Exported PDF: {safe_title}.pdf")
            else:
                error_msg = f"Failed to export PDF {title}: {pdf_response.status_code}"
                result["errors"].append(error_msg)
                logger.error(error_msg)

            # Get and download attachments
            attachments_url = urljoin(self.confluence_url, f"/rest/api/content/{page_id}/child/attachment")
            attachments_response = requests.get(
                attachments_url, auth=(self.username, self.password), verify=self.verify_ssl
            )

            if attachments_response.status_code == 200:
                attachments = attachments_response.json()["results"]
                self.attachment_metadata[page_id] = attachments

                downloaded_files = []
                for attachment in attachments:
                    success, filename = self._download_single_attachment(attachment, safe_title)

                    if success and filename:
                        result["attachments_downloaded"] += 1
                        downloaded_files.append(filename)
                        result["attachment_files"].append(filename)

                        # Count images
                        if any(filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".svg"]):
                            result["images_count"] += 1
                    else:
                        result["attachments_failed"] += 1

                self.downloaded_attachments[title] = downloaded_files

            else:
                error_msg = f"Failed to fetch attachments for {title}: {attachments_response.status_code}"
                result["errors"].append(error_msg)
                logger.error(error_msg)

            # Determine success
            success = result["pdf_exported"] and result["attachments_failed"] == 0
            return success, result

        except Exception as e:
            error_msg = f"Export failed for {title}: {str(e)}"
            result["errors"].append(error_msg)
            logger.error(error_msg)
            return False, result

    def _download_single_attachment(self, attachment: Dict, safe_page_title: str) -> Tuple[bool, Optional[str]]:
        """Download a single attachment with error handling

        Args:
            attachment: Attachment metadata from Confluence API
            safe_page_title: Sanitized page title for filename prefix

        Returns:
            Tuple of (success, filename)
        """
        try:
            download_url = urljoin(self.confluence_url, attachment["_links"]["download"])
            attachment_filename = f"{safe_page_title}_{attachment['title']}"

            attachment_response = requests.get(
                download_url, auth=(self.username, self.password), stream=True, verify=self.verify_ssl
            )

            if attachment_response.status_code == 200:
                attachment_path = f"{self.attachments_dir}/{attachment_filename}"
                with open(attachment_path, "wb") as f:
                    for chunk in attachment_response.iter_content(chunk_size=8192):
                        f.write(chunk)

                logger.info(f"Downloaded attachment: {attachment_filename}")
                return True, attachment_filename
            else:
                logger.error(f"Failed to download attachment: {download_url} - {attachment_response.status_code}")
                return False, None

        except Exception as e:
            logger.error(f"Exception downloading attachment {attachment.get('title', 'unknown')}: {str(e)}")
            return False, None

    def run(self, parent_page_title: str) -> Dict[str, Any]:
        """Run the Confluence download process with comprehensive statistics

        Args:
            parent_page_title: Title of the parent page to start from

        Returns:
            Dictionary with detailed processing results and metadata
        """
        # Ensure directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.attachments_dir, exist_ok=True)

        result: Dict[str, Any] = {
            "parent_page_title": parent_page_title,
            "success": False,
            "pages_processed": [],
            "total_pages": 0,
            "total_pdfs": 0,
            "total_attachments": 0,
            "total_images": 0,
            "errors": [],
        }

        try:
            logger.info("Fetching parent page ID...")
            parent_page_id = self.get_parent_page_id(parent_page_title)
            if not parent_page_id:
                result["errors"].append(f"Could not find parent page: {parent_page_title}")
                return result

            logger.info("Fetching all child pages recursively...")
            all_pages = self.get_children_recursive(parent_page_id)
            result["total_pages"] = len(all_pages)

            logger.info(f"Found {len(all_pages)} pages. Starting export...")

            for page in all_pages:
                try:
                    # Export with comprehensive metadata tracking
                    success, page_result = self.export_pdf_and_attachments(page["id"], page["title"])

                    result["pages_processed"].append(page_result)

                    if success:
                        if page_result.get("pdf_exported"):
                            result["total_pdfs"] += 1
                        result["total_attachments"] += page_result.get("attachments_downloaded", 0)
                        result["total_images"] += page_result.get("images_count", 0)
                    else:
                        result["errors"].extend(page_result.get("errors", []))

                except Exception as e:
                    error_msg = f"Failed to process page {page.get('title', 'unknown')}: {str(e)}"
                    result["errors"].append(error_msg)
                    logger.error(error_msg)

            result["success"] = len(result["errors"]) == 0

            # Final summary
            logger.info("Export completed:")
            logger.info(f"  Pages processed: {len(result['pages_processed'])}")
            logger.info(f"  PDFs exported: {result['total_pdfs']}")
            logger.info(f"  Attachments downloaded: {result['total_attachments']}")
            logger.info(f"  Images found: {result['total_images']}")
            logger.info(f"  Errors: {len(result['errors'])}")

            return result

        except Exception as e:
            error_msg = f"Export run failed: {str(e)}"
            result["errors"].append(error_msg)
            logger.error(error_msg)
            return result
