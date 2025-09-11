"""
Marker Output Cleaner for PDF to Markdown conversion
Fixes common formatting issues introduced by Marker during PDF extraction
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


class MarkerOutputCleaner:
    """Cleans up common formatting issues from Marker PDF extraction"""

    def __init__(self):
        """Initialize the cleaner"""
        pass

    def clean_yaml_structure(self, content: str) -> str:
        """Fix YAML structure corruption caused by Marker

        Marker often misinterprets indented YAML lines as markdown lists,
        adding dashes (-) where they shouldn't be.

        Args:
            content: Raw markdown content from Marker

        Returns:
            Content with YAML structure cleaned up
        """
        if not content:
            return content

        lines = content.split("\n")
        cleaned_lines = []
        in_yaml_block = False
        yaml_block_lines: List[str] = []
        yaml_blocks_found = 0
        yaml_lines_processed = 0

        for line_num, line in enumerate(lines):
            # Check if we're entering or exiting a YAML code block
            if line.strip().startswith("```yaml") or line.strip().startswith("```yml"):
                in_yaml_block = True
                yaml_blocks_found += 1
                cleaned_lines.append(line)
                logger.debug(f"Found YAML block start at line {line_num}: {line.strip()}")
                continue
            elif line.strip() == "```" and in_yaml_block:
                # Process the accumulated YAML block
                if yaml_block_lines:
                    logger.debug(f"Processing YAML block with {len(yaml_block_lines)} lines")
                    cleaned_yaml = self._clean_yaml_block_content(yaml_block_lines)
                    cleaned_lines.extend(cleaned_yaml)
                    yaml_lines_processed += len(yaml_block_lines)
                    yaml_block_lines = []
                in_yaml_block = False
                cleaned_lines.append(line)
                logger.debug(f"YAML block end at line {line_num}")
                continue

            if in_yaml_block:
                # Accumulate YAML lines for processing
                yaml_block_lines.append(line)
            else:
                # Regular content, pass through unchanged
                cleaned_lines.append(line)

        # Handle case where YAML block doesn't have closing ```
        if yaml_block_lines:
            logger.debug(f"Processing final YAML block with {len(yaml_block_lines)} lines")
            cleaned_yaml = self._clean_yaml_block_content(yaml_block_lines)
            cleaned_lines.extend(cleaned_yaml)
            yaml_lines_processed += len(yaml_block_lines)

        result = "\n".join(cleaned_lines)
        logger.info(f"YAML Cleaner: Found {yaml_blocks_found} YAML blocks, processed {yaml_lines_processed} lines")
        return result

    def _clean_yaml_block_content(self, yaml_lines: List[str]) -> List[str]:
        """Clean YAML content that was corrupted by Marker

        Args:
            yaml_lines: List of YAML lines with potential corruption

        Returns:
            List of cleaned YAML lines
        """
        if not yaml_lines:
            return yaml_lines

        cleaned_lines = []

        for line in yaml_lines:
            cleaned_line = self._fix_yaml_line(line)
            cleaned_lines.append(cleaned_line)

        logger.debug(f"Cleaned YAML block with {len(yaml_lines)} lines")
        return cleaned_lines

    def _fix_yaml_line(self, line: str) -> str:
        """Fix a single YAML line corrupted by Marker

        Args:
            line: Single YAML line potentially with corruption

        Returns:
            Cleaned YAML line
        """
        if not line.strip():
            return line

        # NEW PATTERN: Fix incorrect indentation (1 space instead of proper YAML indentation)
        # This is the ACTUAL issue - Marker extracts with wrong spacing

        # SPECIAL CASE: Handle list items that lost their dash
        # Pattern: " - status: value" (1 space before dash)
        list_item_pattern = r"^( )-\s+(.*)$"
        list_match = re.match(list_item_pattern, line)

        if list_match:
            single_space, rest_of_line = list_match.groups()
            # List items in unhealthyConditions should have 2-space indentation
            fixed_line = f"  - {rest_of_line}"
            logger.debug(f"Fixed YAML list item: '{line.strip()}' -> '{fixed_line.strip()}'")
            return fixed_line

        # Pattern: " property: value" (1 space) should be proper YAML indentation
        single_space_pattern = r"^( )([a-zA-Z_][a-zA-Z0-9_./-]*\s*:.*)$"
        match = re.match(single_space_pattern, line)

        if match:
            single_space, rest_of_line = match.groups()

            # Determine correct indentation based on YAML hierarchy
            property_name = rest_of_line.split(":")[0].strip()

            if property_name in ["name", "namespace"]:
                # metadata properties -> 2 spaces
                fixed_line = f"  {rest_of_line}"
            elif property_name in ["maxUnhealthy", "nodeStartupTimeout", "selector", "unhealthyConditions"]:
                # spec properties -> 2 spaces
                fixed_line = f"  {rest_of_line}"
            elif property_name in ["matchLabels"]:
                # nested under selector -> 4 spaces
                fixed_line = f"    {rest_of_line}"
            elif property_name.startswith("machine.openshift.io/"):
                # nested under matchLabels -> 6 spaces
                fixed_line = f"      {rest_of_line}"
            elif property_name in ["timeout", "type"]:
                # These are continuation lines under list items in unhealthyConditions
                # They should align with the list item content (3 spaces after '- ')
                fixed_line = f"    {rest_of_line}"
            else:
                # Default to 2 spaces for unknown properties
                fixed_line = f"  {rest_of_line}"

            logger.debug(
                f"Fixed YAML indentation: '{line.strip()}' -> '{fixed_line.strip()}' "
                f"(1 space -> {len(fixed_line) - len(fixed_line.lstrip())} spaces)"
            )
            return fixed_line

        # LEGACY PATTERNS (keep for backward compatibility)

        # Pattern: "- key: value" where it should be "  key: value"
        # This handles cases where Marker added dashes to indented YAML properties
        yaml_property_pattern = r"^(\s*)-\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$"
        match = re.match(yaml_property_pattern, line)

        if match:
            leading_spaces, property_name, property_value = match.groups()
            # Replace the dash with 2 additional spaces to maintain YAML indentation
            fixed_line = f"{leading_spaces}  {property_name}: {property_value}"
            logger.debug(f"Fixed YAML property: '{line.strip()}' -> '{fixed_line.strip()}'")
            return fixed_line

        # Pattern: "- - key: value" (double dash corruption)
        double_dash_pattern = r"^(\s*)-\s+-\s+(.*)$"
        match = re.match(double_dash_pattern, line)

        if match:
            leading_spaces, rest_of_line = match.groups()
            # This is likely a list item that got double-corrupted
            fixed_line = f"{leading_spaces}  - {rest_of_line}"
            logger.debug(f"Fixed double-dash corruption: '{line.strip()}' -> '{fixed_line.strip()}'")
            return fixed_line

        # SPECIAL CASE: Handle list item continuation lines that got corrupted
        # Pattern: " timeout: 8m" or " type: Ready" after a list item
        list_continuation_pattern = r"^( )(timeout|type):\s*(.*)$"
        match = re.match(list_continuation_pattern, line)

        if match:
            single_space, property_name, property_value = match.groups()
            # These should align with the list item content (4 spaces total)
            fixed_line = f"    {property_name}: {property_value}"
            logger.debug(f"Fixed list continuation: '{line.strip()}' -> '{fixed_line.strip()}'")
            return fixed_line

        # Pattern: "- someValue" where it should be "    someValue" (continuation line)
        continuation_pattern = r"^(\s*)-\s+([^:]+)$"
        match = re.match(continuation_pattern, line)

        if match:
            leading_spaces, continuation_value = match.groups()
            # Check if this looks like a continuation value (no colon, not a typical list item)
            if not continuation_value.strip().startswith(("-", "*", "status:", "timeout:", "type:")):
                fixed_line = f"{leading_spaces}    {continuation_value}"
                logger.debug(f"Fixed continuation line: '{line.strip()}' -> '{fixed_line.strip()}'")
                return fixed_line

        # Return unchanged if no patterns match
        return line

    def clean_marker_output(self, content: str) -> str:
        """Main cleaning method for all Marker output issues

        Args:
            content: Raw markdown content from Marker

        Returns:
            Cleaned content with various formatting issues fixed
        """
        if not content:
            return content

        # Clean YAML structure issues in code blocks
        content = self.clean_yaml_structure(content)

        # ALSO clean raw YAML-like content that's not in code blocks
        content = self.clean_raw_yaml_indentation(content)

        return content

    def clean_raw_yaml_indentation(self, content: str) -> str:
        """Fix YAML indentation in raw text (not in code blocks)

        This handles YAML content that Marker extracts as regular text
        before it gets formatted into code blocks.

        Args:
            content: Raw content from Marker

        Returns:
            Content with YAML indentation fixed
        """
        lines = content.split("\n")
        cleaned_lines = []
        yaml_fixes_applied = 0

        # Look for YAML patterns in the raw text
        for line_num, line in enumerate(lines):
            original_line = line

            # Check if this line looks like YAML with wrong indentation
            if self._is_yaml_like_line(line):
                # Apply the same fixing logic we use for code blocks
                fixed_line = self._fix_yaml_line(line)
                if fixed_line != original_line:
                    yaml_fixes_applied += 1
                    logger.debug(f"Fixed raw YAML line {line_num}: '{line.strip()}' -> '{fixed_line.strip()}'")
                cleaned_lines.append(fixed_line)
            else:
                cleaned_lines.append(line)

        result = "\n".join(cleaned_lines)
        if yaml_fixes_applied > 0:
            logger.info(f"Raw YAML Cleaner: Fixed {yaml_fixes_applied} YAML indentation issues in raw text")

        return result

    def _is_yaml_like_line(self, line: str) -> bool:
        """Check if a line looks like YAML content with potential indentation issues

        Args:
            line: Line to check

        Returns:
            True if this looks like a YAML line that might need fixing
        """
        if not line.strip():
            return False

        # Look for lines that match our YAML patterns
        # Check for single-space indented YAML properties
        if re.match(r"^( )([a-zA-Z_][a-zA-Z0-9_./-]*\s*:.*)$", line):
            return True

        # Check for machine.openshift.io properties
        if re.match(r"^( )(machine\.openshift\.io/.*)$", line):
            return True

        # Check for list continuation patterns
        if re.match(r"^( )(timeout|type):\s*(.*)$", line):
            return True

        return False


def main():
    """Simple CLI test for MarkerOutputCleaner"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python marker_cleaner.py '<corrupted_content>'")
        sys.exit(1)

    cleaner = MarkerOutputCleaner()
    content = sys.argv[1]

    cleaned = cleaner.clean_marker_output(content)

    print("Original content:")
    print(content)
    print("\nCleaned content:")
    print(cleaned)


if __name__ == "__main__":
    main()
