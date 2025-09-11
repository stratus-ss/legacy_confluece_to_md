"""
Unified PDF to Markdown converter with optional image management

Supports both basic PDF conversion and enhanced Confluence integration
with image handling capabilities.
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

try:
    import torch  # type: ignore

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None  # type: ignore

try:
    from .code_formatter import CodeFormatter
    from .marker_cleaner import MarkerOutputCleaner
except ImportError:
    # Handle direct execution
    from code_formatter import CodeFormatter  # type: ignore
    from marker_cleaner import MarkerOutputCleaner  # type: ignore

logger = logging.getLogger(__name__)


class PDFConversionError(Exception):
    """Simple exception for conversion failures"""

    pass


class PDFToMarkdownConverter:
    """PDF conversion utility with comprehensive image management and Confluence integration"""

    def __init__(
        self,
        config_path: Optional[str] = None,
        prefer_gpu: bool = True,
        preserve_indentation: bool = True,
        min_cleanup: bool = True,
    ):
        """Initialize the converter

        Args:
            config_path: Optional path to configuration file (not implemented yet)
            prefer_gpu: Whether to try GPU acceleration first (defaults to True)
            preserve_indentation: Whether to preserve original PDF indentation (True) or standardize (False)
            min_cleanup: If preserve_indentation=True, whether to apply minimal cleanup
        """
        self.config_path = config_path
        self.prefer_gpu = prefer_gpu
        self.preserve_indentation = preserve_indentation
        self.min_cleanup = min_cleanup
        self.device = self._detect_device()
        self.converter = None  # type: ignore
        self.formatter = CodeFormatter(
            preserve_indentation=preserve_indentation,
            min_cleanup=min_cleanup
        )
        self.marker_cleaner = MarkerOutputCleaner()

        indentation_mode = "preserved" if preserve_indentation else "standardized"
        logger.info(f"PDF converter initialized with {indentation_mode} indentation formatting")

    def _detect_device(self) -> str:
        """Detect the best available device for processing

        Returns:
            Device string: 'cuda' if GPU available and preferred, otherwise 'cpu'
        """
        if not self.prefer_gpu:
            logger.info("GPU acceleration disabled by user preference")
            return "cpu"

        if not TORCH_AVAILABLE:
            logger.info("PyTorch not available, falling back to CPU")
            return "cpu"

        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown"
            logger.info(f"🚀 GPU acceleration enabled: {device_name} ({device_count} device(s) available)")
            return "cuda"
        else:
            logger.info("CUDA not available, falling back to CPU")
            return "cpu"

    def _load_converter(self):
        """Load Marker converter lazily with device configuration"""
        if self.converter is None:
            # Set PyTorch device for Marker
            os.environ["TORCH_DEVICE"] = self.device
            logger.info(f"Loading Marker converter and models on device: {self.device}")

            try:
                self.converter = PdfConverter(
                    artifact_dict=create_model_dict(),
                )
                logger.info(f"✅ Converter loaded successfully on {self.device}")
            except Exception as e:
                if self.device == "cuda":
                    logger.warning(f"Failed to load on GPU: {e}")
                    logger.info("Attempting fallback to CPU...")
                    # Force CPU fallback
                    self.device = "cpu"
                    os.environ["TORCH_DEVICE"] = "cpu"
                    try:
                        self.converter = PdfConverter(
                            artifact_dict=create_model_dict(),
                        )
                        logger.info("✅ Converter loaded successfully on CPU (fallback)")
                    except Exception as cpu_error:
                        raise PDFConversionError(f"Failed to load converter on both GPU and CPU: {cpu_error}")
                else:
                    raise PDFConversionError(f"Failed to load converter: {e}")

    def _format_code_blocks(self, markdown_content: str) -> str:
        """Format all code blocks in the markdown content

        Args:
            markdown_content: Raw markdown content with code blocks

        Returns:
            Markdown content with formatted code blocks
        """

        def format_code_block_match(match):
            """Format a single code block match"""
            try:
                # Extract language and content from the match
                language = match.group(1) if match.group(1) else None
                code_content = match.group(2)

                # Format the code block
                formatted_content, detected_language = self.formatter.format_code_block(code_content, language)

                # Return formatted code block with detected language
                return f"```{detected_language}\n{formatted_content}\n```"

            except Exception as e:
                logger.warning(f"Failed to format code block: {e}")
                return match.group(0)  # Return original if formatting fails

        # Pattern to match code blocks: ```optional_language\ncontent\n```
        code_block_pattern = r"```(\w+)?\n(.*?)```"

        # Apply formatting to all code blocks
        formatted_content = re.sub(code_block_pattern, format_code_block_match, markdown_content, flags=re.DOTALL)

        return formatted_content


    def convert_pdf(
        self,
        pdf_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        page_title: Optional[str] = None,
    ) -> Tuple[str, Dict]:
        """Convert a PDF file to markdown with comprehensive image handling

        Args:
            pdf_path: Path to the PDF file to convert
            output_path: Optional output path. If None, returns markdown string
            page_title: Optional page title for image association

        Returns:
            Tuple of (markdown_content, image_summary)

        Raises:
            PDFConversionError: If conversion fails
        """
        try:
            pdf_path = Path(pdf_path)

            # Check if PDF exists
            if not pdf_path.exists():
                raise PDFConversionError(f"PDF file not found: {pdf_path}")

            # Derive page title if not provided
            if not page_title:
                page_title = pdf_path.stem

            logger.info(f"Converting PDF with comprehensive image handling: {pdf_path}")

            # Load converter if needed
            self._load_converter()

            # Convert using Marker
            assert self.converter is not None, "Converter not initialized"
            rendered = self.converter(str(pdf_path))
            full_text, _, images = text_from_rendered(rendered)

            logger.info(f"Conversion completed. Generated {len(full_text)} characters")
            if images:
                logger.info(f"Note: {len(images)} images were found but image processing is disabled")

            # Clean up Marker formatting issues BEFORE code formatting
            full_text = self.marker_cleaner.clean_marker_output(full_text)
            logger.info("Applied Marker output cleaning to fix YAML and structure issues")

            # Apply code block formatting with preserved indentation
            full_text = self._format_code_blocks(full_text)
            logger.info("Code block formatting applied with preserved indentation")

            # Save to file if output path specified
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(full_text)
                logger.info(f"Markdown saved to: {output_path}")

            # Generate simple summary
            summary = {
                "characters_converted": len(full_text),
                "images_detected": len(images) if images else 0,
                "note": "Image processing disabled - images detected but not processed"
            }

            logger.info(f"Conversion summary: {summary}")
            return full_text, summary

        except Exception as e:
            error_msg = f"Failed to convert PDF {pdf_path}: {str(e)}"
            logger.error(error_msg)
            raise PDFConversionError(error_msg) from e

    def batch_convert(
        self, pdf_list: List[Union[str, Path]], output_dir: Union[str, Path], page_titles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Convert multiple PDFs to markdown

        Args:
            pdf_list: List of PDF file paths
            output_dir: Directory to save converted files
            page_titles: Optional list of page titles (must match pdf_list length)

        Returns:
            Dictionary with conversion results
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize results structure
        results: Dict[str, Any] = {
            "success": [],
            "failed": [],
            "stats": {"total_characters": 0, "total_images_detected": 0},
        }

        for idx, pdf_path in enumerate(pdf_list):
            try:
                pdf_path = Path(pdf_path)
                output_file = output_dir / f"{pdf_path.stem}.md"

                # Get page title if provided
                page_title = None
                if page_titles and idx < len(page_titles):
                    page_title = page_titles[idx]

                # Convert PDF to markdown
                markdown_content, conversion_summary = self.convert_pdf(
                    pdf_path=pdf_path, output_path=output_file, page_title=page_title
                )

                results["success"].append(
                    {
                        "pdf_path": str(pdf_path),
                        "output_path": str(output_file),
                        "page_title": page_title or pdf_path.stem,
                        "summary": conversion_summary,
                    }
                )

                # Aggregate statistics
                results["stats"]["total_characters"] += conversion_summary.get("characters_converted", 0)
                results["stats"]["total_images_detected"] += conversion_summary.get("images_detected", 0)

            except PDFConversionError as e:
                logger.error(f"Failed to convert {pdf_path}: {e}")
                results["failed"].append({"pdf_path": str(pdf_path), "error": str(e)})

        # Log results
        total_success = len(results["success"])
        total_failed = len(results["failed"])

        logger.info(f"Batch conversion completed: Success: {total_success}, Failed: {total_failed}")
        logger.info(f"  Total characters converted: {results['stats']['total_characters']}")
        logger.info(f"  Total images detected: {results['stats']['total_images_detected']}")

        return results



def main():
    """Simple CLI test"""
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python converter.py <pdf_path> [output_path]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    converter = PDFToMarkdownConverter()

    try:
        markdown_content, image_summary = converter.convert_pdf(pdf_path, output_path)
        if not output_path:
            print(markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content)
    except PDFConversionError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
