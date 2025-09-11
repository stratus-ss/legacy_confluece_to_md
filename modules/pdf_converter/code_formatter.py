"""
Code Block Formatter for PDF to Markdown conversion
Formats JSON, YAML, and Bash code blocks according to style guides
"""

import json
import logging
import re
from typing import Optional, Tuple

try:
    from .indentation_preserver import IndentationPreserver
except ImportError:
    # Handle direct execution
    from indentation_preserver import IndentationPreserver  # type: ignore

logger = logging.getLogger(__name__)


class CodeFormatter:
    """Configurable code formatter with both standardized and preserved indentation modes"""

    def __init__(self, preserve_indentation: bool = False, min_cleanup: bool = True):
        """Initialize the code formatter
        
        Args:
            preserve_indentation: If True, preserve original PDF indentation instead of standardizing
            min_cleanup: If True and preserve_indentation=True, apply minimal cleanup
        """
        self.preserve_indentation = preserve_indentation
        self.indentation_preserver = IndentationPreserver(min_cleanup=min_cleanup) if preserve_indentation else None
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
                r"\b(echo|if|then|else|elif|fi|for|while|do|done|case|esac|function)\b",  # Bash keywords
                r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=",  # Variable assignments
                r"\[\[.*\]\]",  # Bash conditional expressions
                r"^\s*#(?!\s*[{\[])",  # Comments (but not JSON-like)
            ],
            "go": [
                r"\bpackage\s+\w+",  # Package declaration
                r"\bfunc\s+\w*\s*\(",  # Function declaration
                r"\bimport\s*\(",  # Import statement
                r"\bvar\s+\w+\s+\w+",  # Variable declaration
                r"\b(defer|chan|select|interface|struct|range|map)\b",  # Go-specific keywords
                r":=",  # Short variable declaration
                r"^\s*//",  # Go-style comments
            ],
            "python": [
                r"^def\s+\w+\s*\(",  # Function definition
                r"^class\s+\w+",  # Class definition
                r"\bimport\s+\w+",  # Import statement
                r"\bfrom\s+\w+\s+import",  # From import
                r"\b(print|len|range|str|int|float|list|dict|tuple|set)\s*\(",  # Built-ins
                r"^\s*#(?!\s*[{\[])",  # Python comments
                r":\s*$",  # Colon at end of line (common in Python)
            ],
        }

    def detect_language(self, code_content: str) -> str:
        """Detect the programming language of code content

        Args:
            code_content: Raw code content

        Returns:
            Detected language ('json', 'yaml', 'bash', 'go', 'python', or 'text')
        """
        code_content = code_content.strip()

        if not code_content:
            return "text"

        # Priority 1: Check for strong single indicators first
        if code_content.startswith("#!/bin/bash") or code_content.startswith("#!/bin/sh"):
            return "bash"

        # Also check for common bash script patterns at the start
        if re.match(r"^(VERBOSE|INPUT_FILE|NS)=", code_content, re.MULTILINE):
            return "bash"

        if (code_content.startswith("{") and code_content.endswith("}")) or (
            code_content.startswith("[") and code_content.endswith("]")
        ):
            return "json"

        # Priority 2: Check each language pattern with scoring
        language_scores = {}
        for language, patterns in self.language_patterns.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, code_content, re.MULTILINE | re.IGNORECASE):
                    matches += 1

            language_scores[language] = matches

        # Priority 3: Determine best match
        # For bash, if we have at least 2 matches and it's the highest, choose it
        if language_scores.get("bash", 0) >= 2 and language_scores["bash"] >= max(language_scores.values()):
            return "bash"

        # For other languages, require at least 2 matches
        for language, score in language_scores.items():
            if score >= 2:
                return language

        # Priority 4: Fallback checks
        if any(keyword in code_content.lower() for keyword in ["while", "case", "esac", "done", "echo"]):
            return "bash"

        return "text"

    def format_json(self, content: str, raise_on_error: bool = False) -> str:
        """Format JSON content with 2-space indentation

        Args:
            content: Raw JSON content
            raise_on_error: If True, raise exception on parse error instead of returning original

        Returns:
            Formatted JSON content or original if formatting fails

        Raises:
            json.JSONDecodeError: If raise_on_error=True and JSON is invalid
        """
        try:
            # Parse and reformat with 2-space indentation
            parsed = json.loads(content)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False, sort_keys=True)
            return formatted
        except (json.JSONDecodeError, TypeError) as e:
            if raise_on_error:
                raise
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
        """Format Bash script content with preserved indentation

        Args:
            content: Raw Bash content

        Returns:
            Formatted Bash content with consistent style and proper indentation
        """
        try:
            lines = content.split("\n")
            formatted_lines = []
            indent_level = 0

            # Define keywords that decrease indentation
            decrease_indent_keywords = ["fi", "done", "esac", "}", ";;"]

            # Define keywords that should be at the same level as their opening
            same_level_keywords = ["else", "elif", ";;", "esac"]

            for line in lines:
                stripped = line.strip()

                # Handle empty lines and comments
                if not stripped or stripped.startswith("#"):
                    # Preserve comments and empty lines, but normalize their indentation
                    if stripped.startswith("#"):
                        formatted_lines.append("  " * indent_level + stripped)
                    else:
                        formatted_lines.append("")
                    continue

                # Check if we need to decrease indent before processing this line
                temp_indent = indent_level
                for keyword in same_level_keywords:
                    if stripped.startswith(keyword + " ") or stripped == keyword or stripped.startswith(keyword + ")"):
                        temp_indent = max(0, indent_level - 1)
                        break

                # Special handling for closing keywords
                if (
                    stripped in decrease_indent_keywords
                    or stripped.startswith(";;")
                    or stripped == "}"
                    or stripped.startswith("}")
                    or stripped == "fi"
                    or stripped == "done"
                    or stripped == "esac"
                ):
                    temp_indent = max(0, indent_level - 1)

                # Apply current indentation (2 spaces per level)
                current_indent = "  " * temp_indent

                # Normalize variable references to use ${} syntax where appropriate
                formatted_line = re.sub(
                    r"\$([a-zA-Z_][a-zA-Z0-9_]*)\b(?![}])", r"${\1}", stripped  # $var but not ${var}
                )

                formatted_lines.append(current_indent + formatted_line)

                # Update indent level for next line based on current line
                if (
                    any(stripped.endswith(" " + keyword) or stripped.endswith(keyword) for keyword in ["then", "do"])
                    or stripped.endswith("{")
                    or any(word in stripped.split() for word in ["if", "while", "for", "function"])
                    and (stripped.endswith("then") or stripped.endswith("do"))
                    or re.match(r".*\)\s*$", stripped)
                    and "case" in stripped
                ):
                    indent_level += 1
                elif stripped.startswith("case ") or re.match(r".*\)\s*$", stripped):  # case patterns like "pattern)"
                    if not any(word in stripped for word in decrease_indent_keywords):
                        indent_level += 1
                elif any(stripped.startswith(keyword) or stripped == keyword for keyword in decrease_indent_keywords):
                    indent_level = max(0, indent_level - 1)

            return "\n".join(formatted_lines)

        except Exception as e:
            logger.warning(f"Failed to format Bash: {e}")
            return content

    def format_go(self, content: str) -> str:
        """
        Go formatter following Google Go Style Guide and gofmt conventions
        
        Key principles from Context7:
        - Use gofmt-compatible formatting
        - Match brace indentation in literals
        - Keep function calls on single line when possible
        - Use tabs for indentation (gofmt standard)
        
        Args:
            content: Raw Go code content
            
        Returns:
            Formatted Go code following gofmt standards
        """
        try:
            lines = content.split('\n')
            formatted_lines = []
            indent_level = 0
            
            for line in lines:
                stripped = line.strip()
                
                if not stripped:
                    formatted_lines.append('')
                    continue
                    
                # Handle comments - preserve but apply indentation
                if stripped.startswith('//'):
                    formatted_lines.append('\t' * indent_level + stripped)
                    continue
                    
                # Decrease indent for closing braces
                if stripped in ['}', '}):', '},', '];']:
                    indent_level = max(0, indent_level - 1)
                    
                # Apply tab indentation (Go standard)
                formatted_line = '\t' * indent_level + stripped
                formatted_lines.append(formatted_line)
                
                # Increase indent after opening braces, function declarations, control structures
                if (stripped.endswith('{') or 
                    (stripped.endswith('(') and len(stripped) > 10) or  # Long function calls
                    stripped.endswith('[') or
                    re.match(r'^(if|for|func|switch|select|type|struct)\b.*{$', stripped) or
                    re.match(r'^(func)\b.*\($', stripped)):  # Function parameters spread across lines
                    indent_level += 1
                    
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            logger.warning(f"Failed to format Go: {e}")
            return content

    def format_python(self, content: str) -> str:
        """
        Python formatter following PEP 8 standards from Context7
        
        Key principles:
        - Use 4 spaces for indentation (never tabs)
        - Hanging indents should add a level (4 spaces)
        - No spaces inside parentheses/brackets/braces
        - Proper continuation line alignment
        
        Args:
            content: Raw Python code content
            
        Returns:
            PEP 8 compliant formatted Python code
        """
        try:
            lines = content.split('\n')
            formatted_lines = []
            indent_level = 0
            
            for line_idx, line in enumerate(lines):
                stripped = line.strip()
                
                if not stripped:
                    formatted_lines.append('')
                    continue
                    
                # Handle comments - preserve but apply indentation
                if stripped.startswith('#'):
                    formatted_lines.append('    ' * indent_level + stripped)
                    continue
                    
                # Handle dedenting keywords (they go back one level)
                if re.match(r'^(else|elif|except|finally|case)\b', stripped):
                    # These keywords dedent one level from current
                    indent_level = max(0, indent_level - 1)
                elif stripped in [')', ']', '}']:
                    # Closing brackets dedent
                    indent_level = max(0, indent_level - 1)
                    
                # Apply current indentation level
                formatted_line = '    ' * indent_level + stripped
                formatted_lines.append(formatted_line)
                
                # Increase indent after lines ending with colon (blocks)
                if stripped.endswith(':') and not stripped.startswith('#'):
                    indent_level += 1
                # Also handle opening brackets
                elif stripped.endswith('(') or stripped.endswith('[') or stripped.endswith('{'):
                    indent_level += 1
                    
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            logger.warning(f"Failed to format Python: {e}")
            return content

    def format_code_block(self, content: str, language: Optional[str] = None) -> Tuple[str, str]:
        """Format a code block with configurable indentation handling

        Args:
            content: Raw code content
            language: Optional language hint

        Returns:
            Tuple of (formatted_content, detected_language)
        """
        # For programming languages, ALWAYS apply proper formatting for readability
        # Even in preservation mode, code blocks benefit from standardized formatting
        detected_language = language if language else self.detect_language(content)
        
        # Apply language-specific formatting if we recognize the language
        if detected_language in ["bash", "python", "go", "json", "yaml"]:
            logger.debug(f"Applying {detected_language} formatter (override preservation for code blocks)")
            # Skip preservation mode for recognized programming languages
            pass  # Continue to standardized formatting below
        elif self.preserve_indentation and self.indentation_preserver:
            # Only use preservation for unrecognized content/text
            return self.indentation_preserver.format_with_preserved_indentation(content, language)
        
        # Fall back to original standardized formatting
        # If language is provided, try it first, but detect if it fails
        original_language = language
        if not language:
            language = self.detect_language(content)

        # Format based on language with fallback detection
        formatted_content = content
        final_language = language

        if language == "json":
            try:
                formatted_content = self.format_json(content, raise_on_error=True)
            except Exception:
                # JSON formatting failed, try auto-detection
                logger.info("JSON formatting failed, attempting language re-detection")
                detected = self.detect_language(content)
                if detected != "json":
                    final_language = detected
                    if detected == "bash":
                        formatted_content = self.format_bash(content)
                    elif detected == "yaml":
                        formatted_content = self.format_yaml(content)
                    else:
                        formatted_content = content
                else:
                    # Keep original content if detection still says JSON
                    formatted_content = content
        elif language == "yaml":
            formatted_content = self.format_yaml(content)
        elif language == "bash":
            formatted_content = self.format_bash(content)
        elif language == "go":
            formatted_content = self.format_go(content)
        elif language == "python":
            formatted_content = self.format_python(content)
        else:
            # Try auto-detection for unknown languages
            detected = self.detect_language(content)
            if detected in ["json", "yaml", "bash", "go", "python"]:
                final_language = detected
                if detected == "json":
                    formatted_content = self.format_json(content)
                elif detected == "yaml":
                    formatted_content = self.format_yaml(content)
                elif detected == "bash":
                    formatted_content = self.format_bash(content)
                elif detected == "go":
                    formatted_content = self.format_go(content)
                elif detected == "python":
                    formatted_content = self.format_python(content)
            else:
                # No formatting for truly unknown languages
                formatted_content = content

        logger.debug(f"Formatted code block ({'preserved' if self.preserve_indentation else 'standardized'}): {original_language} -> {final_language}")
        return formatted_content, final_language


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
