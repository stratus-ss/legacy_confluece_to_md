"""
Unified Configuration System for PDF to Markdown Converter

Combines simple dict-based configuration with enhanced dataclass-based system
for backward compatibility and future extensibility.
"""

import logging
import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


# =============================================================================
# ENVIRONMENT VARIABLE HELPERS
# =============================================================================


def _get_bool_env(env_var: str, default: bool) -> bool:
    """Get boolean value from environment variable"""
    load_dotenv()  # Ensure .env is loaded
    return os.getenv(env_var, str(default)).lower() == "true"


def _get_int_env(env_var: str, default: int) -> int:
    """Get integer value from environment variable"""
    load_dotenv()
    env_value = os.getenv(env_var)
    if env_value is None:
        return default
    try:
        return int(env_value)
    except ValueError:
        logger.warning(f"Invalid integer value for {env_var}='{env_value}', using default: {default}")
        return default


def _get_float_env(env_var: str, default: float) -> float:
    """Get float value from environment variable"""
    load_dotenv()
    env_value = os.getenv(env_var)
    if env_value is None:
        return default
    try:
        return float(env_value)
    except ValueError:
        logger.warning(f"Invalid float value for {env_var}='{env_value}', using default: {default}")
        return default


def _get_str_env(env_var: str, default: str) -> str:
    """Get string value from environment variable"""
    load_dotenv()
    return os.getenv(env_var, default)


def _get_list_env(env_var: str, default: List[str]) -> List[str]:
    """Get list value from comma-separated environment variable"""
    load_dotenv()
    env_value = os.getenv(env_var)
    if env_value:
        return [item.strip() for item in env_value.split(",")]
    return default


# =============================================================================
# ENHANCED CONFIGURATION SYSTEM (Dataclass-based)
# =============================================================================


@dataclass
class ConverterConfig:
    """Unified configuration for PDF to Markdown conversion"""

    # Original converter settings (backward compatible)
    prefer_gpu: bool = field(default_factory=lambda: _get_bool_env("PDF_PREFER_GPU", True))
    log_level: str = field(default_factory=lambda: _get_str_env("PDF_LOG_LEVEL", "INFO"))
    output_format: str = field(default_factory=lambda: _get_str_env("PDF_OUTPUT_FORMAT", "markdown"))

    # Code formatting settings
    format_code_blocks: bool = field(default_factory=lambda: _get_bool_env("PDF_FORMAT_CODE_BLOCKS", True))
    preserve_indentation: bool = field(default_factory=lambda: _get_bool_env("PDF_PRESERVE_INDENTATION", True))
    min_cleanup: bool = field(default_factory=lambda: _get_bool_env("PDF_MIN_CLEANUP", True))
    detect_languages: bool = field(default_factory=lambda: _get_bool_env("PDF_DETECT_LANGUAGES", True))
    supported_languages: List[str] = field(
        default_factory=lambda: _get_list_env("PDF_SUPPORTED_LANGUAGES", ["json", "yaml", "bash", "go", "python"])
    )

    # Output settings
    output_dir: str = field(default_factory=lambda: _get_str_env("PDF_OUTPUT_DIR", "output/markdown"))
    include_metadata: bool = field(default_factory=lambda: _get_bool_env("PDF_INCLUDE_METADATA", False))

    # Processing settings
    timeout: int = field(default_factory=lambda: _get_int_env("PDF_TIMEOUT", 300))
    max_file_size_mb: int = field(default_factory=lambda: _get_int_env("PDF_MAX_FILE_SIZE_MB", 100))

    # Confluence integration
    capture_attachment_metadata: bool = field(
        default_factory=lambda: _get_bool_env("PDF_CAPTURE_ATTACHMENT_METADATA", True)
    )
    save_metadata_reports: bool = field(default_factory=lambda: _get_bool_env("PDF_SAVE_METADATA_REPORTS", True))

    # Performance settings
    batch_size: int = field(default_factory=lambda: _get_int_env("PDF_BATCH_SIZE", 10))
    memory_limit_mb: int = field(default_factory=lambda: _get_int_env("PDF_MEMORY_LIMIT_MB", 2048))

    def __post_init__(self):
        """Validate configuration after creation"""
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


# =============================================================================
# CONFIGURATION LOADING FUNCTIONS
# =============================================================================


def load_config(
    config_path: Optional[str] = None, return_dataclass: bool = False
) -> Union[Dict[str, Any], ConverterConfig]:
    """Unified configuration loader with optional enhanced features

    Args:
        config_path: Path to YAML configuration file (enhanced mode only)
        return_dataclass: If True, returns ConverterConfig object; if False, returns dict

    Returns:
        Configuration dict (legacy format) or ConverterConfig object
    """
    if not return_dataclass:
        # Legacy mode - return simple dict from environment variables
        load_dotenv()

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
                "timeout": _get_int_env("PDF_TIMEOUT", 300),
                "max_file_size_mb": _get_int_env("PDF_MAX_FILE_SIZE_MB", 100),
            },
        }
    else:
        # Dataclass mode - load from file and environment, return dataclass
        return _load_dataclass_config_impl(config_path)


def _load_dataclass_config_impl(config_path: Optional[str] = None) -> ConverterConfig:
    """Internal implementation for dataclass configuration loading

    Args:
        config_path: Path to YAML configuration file

    Returns:
        ConverterConfig object with full feature set
    """
    # Default configuration
    config_dict = {}

    # Load from file if specified
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f) or {}
                config_dict.update(file_config)
            logger.info(f"Loaded configuration from: {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load config file {config_path}: {e}")

    # Override with environment variables
    env_config = _load_config_from_env()
    if env_config:
        config_dict.update(env_config)

    # Create configuration object
    config = ConverterConfig(**config_dict)

    logger.info("Configuration loaded successfully")
    return config


def _load_config_from_env() -> Dict:
    """Load configuration from environment variables (internal helper)"""
    load_dotenv()
    config = {}

    # Main converter settings
    if os.getenv("PDF_PREFER_GPU"):
        config["prefer_gpu"] = os.getenv("PDF_PREFER_GPU", "true").lower() == "true"

    if os.getenv("PDF_LOG_LEVEL"):
        config["log_level"] = os.getenv("PDF_LOG_LEVEL", "INFO").upper()

    if os.getenv("PDF_FORMAT_CODE_BLOCKS"):
        config["format_code_blocks"] = os.getenv("PDF_FORMAT_CODE_BLOCKS", "true").lower() == "true"

    # Output settings
    if os.getenv("PDF_OUTPUT_DIR"):
        config["output_dir"] = os.getenv("PDF_OUTPUT_DIR", "output/markdown")

    if os.getenv("PDF_INCLUDE_METADATA"):
        config["include_metadata"] = os.getenv("PDF_INCLUDE_METADATA", "false").lower() == "true"

    # Processing settings
    if os.getenv("PDF_TIMEOUT"):
        config["timeout"] = _get_int_env("PDF_TIMEOUT", 300)

    if os.getenv("PDF_MAX_FILE_SIZE_MB"):
        config["max_file_size_mb"] = _get_int_env("PDF_MAX_FILE_SIZE_MB", 100)

    # Supported languages
    if os.getenv("PDF_SUPPORTED_LANGUAGES"):
        supported_languages_str = os.getenv("PDF_SUPPORTED_LANGUAGES", "json,yaml,bash")
        config["supported_languages"] = [lang.strip() for lang in supported_languages_str.split(",")]

    return config


def create_sample_config_file(output_path: str = "pdf_converter_config.yaml"):
    """Create a sample YAML configuration file

    Args:
        output_path: Path where to save the sample config file
    """
    sample_config = {
        "prefer_gpu": True,
        "log_level": "INFO",
        "output_format": "markdown",
        "format_code_blocks": True,
        "detect_languages": True,
        "supported_languages": ["json", "yaml", "bash"],
        "output_dir": "output/markdown",
        "include_metadata": False,
        "timeout": 300,
        "max_file_size_mb": 100,
        "capture_attachment_metadata": True,
        "save_metadata_reports": True,
        "batch_size": 10,
        "memory_limit_mb": 2048,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)

    print(f"Sample configuration saved to: {output_path}")


# =============================================================================
# LOGGING SETUP
# =============================================================================


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None, enhanced_format: bool = False):
    """Unified logging setup with optional enhanced features

    Args:
        log_level: Logging level
        log_file: Optional file path for logging output (enhanced mode)
        enhanced_format: If True, use detailed format; if False, use simple format
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    if not enhanced_format and not log_file:
        # Legacy mode - simple format, console only
        logging.basicConfig(level=level, format="%(levelname)s: %(message)s", handlers=[logging.StreamHandler()])
    else:
        # Enhanced mode - detailed format with optional file output
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Create handlers
        handlers = [logging.StreamHandler()]

        if log_file:
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
