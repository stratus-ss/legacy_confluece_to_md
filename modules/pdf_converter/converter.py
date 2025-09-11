"""
Simple PDF to Markdown converter using Marker
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional, Union
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None  # type: ignore

try:
    from .code_formatter import CodeFormatter
except ImportError:
    # Handle direct execution
    from code_formatter import CodeFormatter  # type: ignore

logger = logging.getLogger(__name__)


class PDFConversionError(Exception):
    """Simple exception for conversion failures"""

    pass


class PDFToMarkdownConverter:
    """Independent PDF conversion utility using Marker"""

    def __init__(self, config_path: Optional[str] = None, prefer_gpu: bool = True):
        """Initialize the converter

        Args:
            config_path: Optional path to configuration file (not implemented yet)
            prefer_gpu: Whether to try GPU acceleration first (defaults to True)
        """
        self.config_path = config_path
        self.prefer_gpu = prefer_gpu
        self.device = self._detect_device()
        self.converter = None  # type: ignore
        self.formatter = CodeFormatter()

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

    def convert_pdf(self, pdf_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> str:
        """Convert a PDF file to markdown

        Args:
            pdf_path: Path to the PDF file to convert
            output_path: Optional output path. If None, returns markdown string

        Returns:
            Converted markdown content

        Raises:
            PDFConversionError: If conversion fails
        """
        try:
            pdf_path = Path(pdf_path)

            # Check if PDF exists
            if not pdf_path.exists():
                raise PDFConversionError(f"PDF file not found: {pdf_path}")

            logger.info(f"Converting PDF: {pdf_path}")

            # Load converter if needed
            self._load_converter()

            # Convert using Marker
            assert self.converter is not None, "Converter not initialized"
            rendered = self.converter(str(pdf_path))
            full_text, _, images = text_from_rendered(rendered)

            logger.info(f"Conversion completed. Generated {len(full_text)} characters")

            # Apply code block formatting
            full_text = self._format_code_blocks(full_text)
            logger.info("Code block formatting applied")

            # Save to file if output path specified
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(full_text)
                logger.info(f"Markdown saved to: {output_path}")

            return full_text

        except Exception as e:
            error_msg = f"Failed to convert PDF {pdf_path}: {str(e)}"
            logger.error(error_msg)
            raise PDFConversionError(error_msg) from e

    def batch_convert(self, pdf_list: list, output_dir: Union[str, Path]) -> dict:
        """Convert multiple PDFs to markdown

        Args:
            pdf_list: List of PDF file paths
            output_dir: Directory to save converted files

        Returns:
            Dictionary with results: {'success': [files], 'failed': [files]}
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results: dict = {"success": [], "failed": []}

        for pdf_path in pdf_list:
            try:
                pdf_path = Path(pdf_path)
                output_file = output_dir / f"{pdf_path.stem}.md"

                self.convert_pdf(pdf_path, output_file)
                results["success"].append(str(pdf_path))

            except PDFConversionError as e:
                logger.error(f"Failed to convert {pdf_path}: {e}")
                results["failed"].append(str(pdf_path))

        logger.info(f"Batch conversion completed. Success: {len(results['success'])}, Failed: {len(results['failed'])}")
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
        result = converter.convert_pdf(pdf_path, output_path)
        if not output_path:
            print(result[:500] + "..." if len(result) > 500 else result)
    except PDFConversionError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
