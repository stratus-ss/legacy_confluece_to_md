"""
Configuration utilities for PDF to Markdown converter
"""

import logging
import os
from typing import Dict, Any

from dotenv import load_dotenv


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables

    Returns:
        Configuration dictionary with defaults
    """
    # Load environment variables from .env file
    load_dotenv()

    # Parse supported languages from comma-separated string
    supported_languages_str = os.getenv("PDF_SUPPORTED_LANGUAGES", "json,yaml,bash")
    supported_languages = [lang.strip() for lang in supported_languages_str.split(",")]

    return {
        "converter": {
            "format_code_blocks": os.getenv("PDF_FORMAT_CODE_BLOCKS", "true").lower() == "true",
            "prefer_gpu": os.getenv("PDF_PREFER_GPU", "true").lower() == "true",
            "supported_languages": supported_languages,
            "log_level": os.getenv("PDF_LOG_LEVEL", "INFO").upper(),
        },
        "output": {
            "output_dir": os.getenv("PDF_OUTPUT_DIR", "output/markdown"),
            "include_metadata": os.getenv("PDF_INCLUDE_METADATA", "false").lower() == "true",
        },
        "processing": {
            "timeout": int(os.getenv("PDF_TIMEOUT", "300")),
            "max_file_size_mb": int(os.getenv("PDF_MAX_FILE_SIZE_MB", "100")),
        },
    }


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration

    Args:
        log_level: Logging level
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s", handlers=[logging.StreamHandler()])
