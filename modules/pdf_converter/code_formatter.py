"""
Code Block Formatter for PDF to Markdown conversion
Formats JSON, YAML, and Bash code blocks according to style guides
"""

import json
import logging
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class CodeFormatter:
    """Simple code formatter with basic language detection"""

    def __init__(self):
        """Initialize the code formatter"""
        self.language_patterns = {
            "json": [
                r"^\s*[{\[]",  # Starts with { or [
                r'["\']:\s*["\']',  # Key-value pairs with quotes
                r"\}\s*,?\s*$",  # Ends with }
            ],
            "yaml": [
                r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*:",  # Key: value
                r"^\s*-\s+",  # List items
                r":\s*[|\>]",  # Block scalars
            ],
            "bash": [
                r"#!/bin/(bash|sh)",  # Shebang
                r"\$\{?[a-zA-Z_][a-zA-Z0-9_]*\}?",  # Variables
                r"\becho\b|\bif\b|\bfor\b|\bwhile\b",  # Common bash keywords
            ],
        }

    def detect_language(self, code_content: str) -> str:
        """Detect the programming language of code content

        Args:
            code_content: Raw code content

        Returns:
            Detected language ('json', 'yaml', 'bash', or 'text')
        """
        code_content = code_content.strip()

        if not code_content:
            return "text"

        # Check each language pattern
        for language, patterns in self.language_patterns.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, code_content, re.MULTILINE | re.IGNORECASE):
                    matches += 1

            # If at least 2 patterns match, consider it that language
            if matches >= 2:
                return language

        # Check for single strong indicators
        if code_content.startswith("#!/bin/"):
            return "bash"

        if (code_content.startswith("{") and code_content.endswith("}")) or (
            code_content.startswith("[") and code_content.endswith("]")
        ):
            return "json"

        return "text"

    def format_json(self, content: str) -> str:
        """Format JSON content with 2-space indentation

        Args:
            content: Raw JSON content

        Returns:
            Formatted JSON content or original if formatting fails
        """
        try:
            # Parse and reformat with 2-space indentation
            parsed = json.loads(content)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False, sort_keys=True)
            return formatted
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to format JSON: {e}")
            return content

    def format_yaml(self, content: str) -> str:
        """Format YAML content with proper alignment

        Args:
            content: Raw YAML content

        Returns:
            Formatted YAML content (basic formatting)
        """
        try:
            lines = content.split("\n")
            formatted_lines = []

            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    # Preserve empty lines and comments
                    formatted_lines.append(stripped)
                    continue

                # Basic indentation normalization (2 spaces per level)
                indent_level = len(line) - len(line.lstrip())
                normalized_indent = (indent_level // 2) * 2  # Round to even number

                if ":" in stripped and not stripped.startswith("-"):
                    # Key-value pair
                    key, value = stripped.split(":", 1)
                    formatted_line = " " * normalized_indent + f"{key.strip()}: {value.strip()}"
                elif stripped.startswith("-"):
                    # List item
                    item_content = stripped[1:].strip()
                    formatted_line = " " * normalized_indent + f"- {item_content}"
                else:
                    # Other content
                    formatted_line = " " * normalized_indent + stripped

                formatted_lines.append(formatted_line)

            return "\n".join(formatted_lines)

        except Exception as e:
            logger.warning(f"Failed to format YAML: {e}")
            return content

    def format_bash(self, content: str) -> str:
        """Format Bash script content

        Args:
            content: Raw Bash content

        Returns:
            Formatted Bash content with consistent style
        """
        try:
            lines = content.split("\n")
            formatted_lines = []

            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    # Preserve empty lines and comments as-is
                    formatted_lines.append(stripped)
                    continue

                # Normalize variable references to use ${} syntax
                # Simple pattern replacement for common cases
                formatted_line = re.sub(
                    r"\$([a-zA-Z_][a-zA-Z0-9_]*)\b(?![}])", r"${\1}", stripped  # $var but not ${var}
                )

                formatted_lines.append(formatted_line)

            return "\n".join(formatted_lines)

        except Exception as e:
            logger.warning(f"Failed to format Bash: {e}")
            return content

    def format_code_block(self, content: str, language: Optional[str] = None) -> Tuple[str, str]:
        """Format a code block with language detection

        Args:
            content: Raw code content
            language: Optional language hint

        Returns:
            Tuple of (formatted_content, detected_language)
        """
        # Detect language if not provided
        if not language:
            language = self.detect_language(content)

        # Format based on language
        if language == "json":
            formatted_content = self.format_json(content)
        elif language == "yaml":
            formatted_content = self.format_yaml(content)
        elif language == "bash":
            formatted_content = self.format_bash(content)
        else:
            # No formatting for unknown languages
            formatted_content = content

        logger.debug(f"Formatted code block as {language}")
        return formatted_content, language


def main():
    """Simple CLI test for CodeFormatter"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python code_formatter.py '<code_content>' [language]")
        sys.exit(1)

    formatter = CodeFormatter()
    content = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else None

    formatted, detected = formatter.format_code_block(content, language)

    print(f"Detected language: {detected}")
    print("Formatted code:")
    print(formatted)


if __name__ == "__main__":
    main()
