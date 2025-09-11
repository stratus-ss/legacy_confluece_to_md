"""
Indentation Preservation for PDF to Markdown conversion
Preserves original PDF text indentation instead of applying standardized formatting
"""

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class IndentationPreserver:
    """Preserves original PDF text indentation patterns while providing minimal cleanup"""

    def __init__(self, min_cleanup: bool = True):
        """Initialize the indentation preserver

        Args:
            min_cleanup: If True, applies minimal cleanup (removes excessive blank lines, etc.)
        """
        self.min_cleanup = min_cleanup

    def analyze_indentation_pattern(self, content: str) -> Dict[str, Any]:
        """Analyze the indentation pattern in the content

        Args:
            content: The text content to analyze

        Returns:
            Dictionary with indentation analysis results
        """
        lines = content.split("\n")
        indentation_info: Dict[str, Any] = {
            "uses_tabs": False,
            "uses_spaces": False,
            "common_indent_sizes": [],
            "mixed_indentation": False,
            "total_lines": len(lines),
            "indented_lines": 0,
        }

        indent_sizes = []

        for line in lines:
            if not line.strip():  # Skip empty lines
                continue

            # Count leading whitespace
            leading_whitespace = len(line) - len(line.lstrip())
            if leading_whitespace > 0:
                indentation_info["indented_lines"] += 1
                indent_sizes.append(leading_whitespace)

                # Check for tabs vs spaces
                if line.startswith("\t"):
                    indentation_info["uses_tabs"] = True
                elif line.startswith(" "):
                    indentation_info["uses_spaces"] = True

        # Determine most common indentation sizes
        if indent_sizes:
            from collections import Counter

            size_counts = Counter(indent_sizes)
            indentation_info["common_indent_sizes"] = [size for size, count in size_counts.most_common(3)]

        # Check for mixed indentation
        indentation_info["mixed_indentation"] = indentation_info["uses_tabs"] and indentation_info["uses_spaces"]

        return indentation_info

    def preserve_indentation(self, content: str, language_hint: Optional[str] = None) -> Tuple[str, str]:
        """Preserve original indentation with absolute fidelity to PDF structure

        Args:
            content: Raw code content with original indentation
            language_hint: Optional language hint for minimal language-specific handling

        Returns:
            Tuple of (preserved_content, detected_language_or_hint)
        """
        if not content.strip():
            return content, language_hint or "text"

        lines = content.split("\n")
        preserved_lines = []

        # Analyze indentation pattern
        indent_info = self.analyze_indentation_pattern(content)
        logger.debug(f"Indentation analysis: {indent_info}")

        # Preserve each line's original indentation with MAXIMUM fidelity
        for line in lines:
            if self.min_cleanup:
                # Only remove trailing whitespace, preserve ALL leading whitespace exactly
                if not line.strip():
                    # Preserve empty lines as truly empty (but don't mess with leading spaces on empty lines from PDF)
                    preserved_lines.append("")
                else:
                    # Preserve ALL leading whitespace exactly as it appears in PDF
                    # Only strip trailing whitespace to avoid line ending issues
                    preserved_line = line.rstrip()
                    preserved_lines.append(preserved_line)
            else:
                # Preserve everything exactly as-is, including trailing spaces
                preserved_lines.append(line)

        preserved_content = "\n".join(preserved_lines)

        # Optional: Try to detect language if not provided
        if not language_hint:
            language_hint = self._simple_language_detection(preserved_content)

        logger.debug(
            f"Preserved indentation with maximum fidelity for {len(lines)} lines, detected language: {language_hint}"
        )
        return preserved_content, language_hint

    def _simple_language_detection(self, content: str) -> str:
        """Simple language detection without affecting indentation

        Args:
            content: The content to analyze

        Returns:
            Detected language string
        """
        content_lower = content.lower()

        # Quick detection patterns that don't rely on indentation
        if content.startswith("#!/bin/bash") or content.startswith("#!/bin/sh"):
            return "bash"
        elif content.strip().startswith("{") and content.strip().endswith("}"):
            return "json"
        elif content.strip().startswith("[") and content.strip().endswith("]"):
            return "json"
        elif "echo " in content_lower or "if [" in content_lower or "$(" in content:
            return "bash"
        elif "---" in content or "apiVersion:" in content or "kind:" in content:
            return "yaml"

        return "text"

    def format_with_preserved_indentation(self, content: str, language: Optional[str] = None) -> Tuple[str, str]:
        """Main method to format content while preserving indentation

        Args:
            content: Raw content to format
            language: Optional language hint

        Returns:
            Tuple of (formatted_content, final_language)
        """
        return self.preserve_indentation(content, language)
