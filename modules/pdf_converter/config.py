"""
Environment-based Configuration System for PDF to Markdown Converter

Provides both dict-based configuration (for backward compatibility) and
dataclass-based configuration, both loaded from environment variables only.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables once at module level
load_dotenv()


def _safe_int(value: str, default: int) -> int:
    """Safely convert string to integer with default fallback"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


@dataclass
class ConverterConfig:
    """Environment-based configuration for PDF to Markdown conversion"""

    # Original converter settings (backward compatible)
    prefer_gpu: bool = os.getenv("PDF_PREFER_GPU", "true").lower() == "true"
    log_level: str = os.getenv("PDF_LOG_LEVEL", "INFO")
    output_format: str = os.getenv("PDF_OUTPUT_FORMAT", "markdown")

    # Code formatting settings
    format_code_blocks: bool = os.getenv("PDF_FORMAT_CODE_BLOCKS", "true").lower() == "true"
    preserve_indentation: bool = os.getenv("PDF_PRESERVE_INDENTATION", "true").lower() == "true"
    min_cleanup: bool = os.getenv("PDF_MIN_CLEANUP", "true").lower() == "true"
    detect_languages: bool = os.getenv("PDF_DETECT_LANGUAGES", "true").lower() == "true"
    supported_languages: List[str] = field(
        default_factory=lambda: [
            lang.strip() for lang in os.getenv("PDF_SUPPORTED_LANGUAGES", "json,yaml,bash,go,python").split(",")
        ]
    )

    # Output settings
    output_dir: str = os.getenv("PDF_OUTPUT_DIR", "output/markdown")
    include_metadata: bool = os.getenv("PDF_INCLUDE_METADATA", "false").lower() == "true"

    # Processing settings
    timeout: int = _safe_int(os.getenv("PDF_TIMEOUT", "300"), 300)
    max_file_size_mb: int = _safe_int(os.getenv("PDF_MAX_FILE_SIZE_MB", "100"), 100)

    # Confluence integration
    capture_attachment_metadata: bool = os.getenv("PDF_CAPTURE_ATTACHMENT_METADATA", "true").lower() == "true"
    save_metadata_reports: bool = os.getenv("PDF_SAVE_METADATA_REPORTS", "true").lower() == "true"

    # Performance settings
    batch_size: int = _safe_int(os.getenv("PDF_BATCH_SIZE", "10"), 10)
    memory_limit_mb: int = _safe_int(os.getenv("PDF_MEMORY_LIMIT_MB", "2048"), 2048)

    def __post_init__(self):
        """Validate configuration after creation"""
        # Validate log level
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_log_levels:
            logger.warning(f"Invalid log_level '{self.log_level}', using 'INFO'")
            self.log_level = "INFO"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for backward compatibility

        Returns:
            Configuration in the original dict format
        """
        return {
            "converter": {
                "format_code_blocks": self.format_code_blocks,
                "prefer_gpu": self.prefer_gpu,
                "supported_languages": self.supported_languages,
                "log_level": self.log_level,
            },
            "output": {
                "output_dir": self.output_dir,
                "include_metadata": self.include_metadata,
            },
            "processing": {
                "timeout": self.timeout,
                "max_file_size_mb": self.max_file_size_mb,
            },
        }


def load_config(return_dataclass: bool = False) -> Union[Dict[str, Any], ConverterConfig]:
    """Load configuration from environment variables only

    Args:
        return_dataclass: If True, returns ConverterConfig object; if False, returns dict

    Returns:
        Configuration dict (legacy format) or ConverterConfig object
    """
    if return_dataclass:
        # Dataclass mode - load from environment variables only
        return ConverterConfig()

    # Legacy mode - return simple dict from environment variables
    # Parse supported languages from comma-separated string
    supported_languages_str = os.getenv("PDF_SUPPORTED_LANGUAGES", "json,yaml,bash")
    supported_languages = [lang.strip() for lang in supported_languages_str.split(",")]

    return {
        "converter": {
            "format_code_blocks": os.getenv("PDF_FORMAT_CODE_BLOCKS", "true").lower() == "true",
            "preserve_indentation": os.getenv("PDF_PRESERVE_INDENTATION", "true").lower() == "true",
            "min_cleanup": os.getenv("PDF_MIN_CLEANUP", "true").lower() == "true",
            "prefer_gpu": os.getenv("PDF_PREFER_GPU", "true").lower() == "true",
            "supported_languages": supported_languages,
            "log_level": os.getenv("PDF_LOG_LEVEL", "INFO").upper(),
        },
        "output": {
            "output_dir": os.getenv("PDF_OUTPUT_DIR", "output/markdown"),
            "include_metadata": os.getenv("PDF_INCLUDE_METADATA", "false").lower() == "true",
        },
        "processing": {
            "timeout": _safe_int(os.getenv("PDF_TIMEOUT", "300"), 300),
            "max_file_size_mb": _safe_int(os.getenv("PDF_MAX_FILE_SIZE_MB", "100"), 100),
        },
    }


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Setup logging with configurable level and optional file output

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging output
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    if not log_file:
        # Console only logging
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", handlers=[logging.StreamHandler()])
    else:
        # Console and file logging with detailed format
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Create handlers
        handlers: List[logging.Handler] = [logging.StreamHandler()]

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

        # Configure root logger
        logging.basicConfig(
            level=level, handlers=handlers, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Reduce noise from some libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
