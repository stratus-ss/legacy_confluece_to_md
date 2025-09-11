# Confluence to Markdown Converter

A comprehensive Python tool for downloading PDFs from Confluence and converting them to clean, formatted Markdown. This project includes both Confluence Server/Datacenter integration for automated content retrieval and advanced PDF-to-Markdown conversion with intelligent code block formatting.

## 🚀 Features

### Confluence Integration
- **Recursive Download**: Downloads all child pages under a parent page
- **PDF Export**: Exports Confluence pages as PDF files
- **Attachment Support**: Downloads all attachments for each page
- **Environment-based Config**: Secure credential management via environment variables

### PDF to Markdown Conversion
- **Advanced PDF Processing**: Uses Marker library with GPU acceleration support
- **Intelligent Code Formatting**: Automatic detection and formatting of JSON, YAML, Bash, Python, and Go code blocks
- **Attachment Processing**: Handles Confluence attachments with organized directory structure
- **Batch Processing**: Convert multiple PDFs with concurrent processing
- **Performance Optimization**: Memory management, timeouts, and resource limits
- **Configurable Output**: Environment-based configuration with extensive customization
- **CLI Interface**: Full command-line interface with Click framework

## 📋 Requirements

- Python 3.9+ (tested up to Python 3.13)
- Virtual environment (recommended)
- Access to a Confluence Server or DataCenter instance
- Optional: CUDA-compatible GPU for faster PDF processing

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/stratus-ss/legacy_confluece_to_md
cd legacy_confluece_to_md
```

### 2. Create Virtual Environment
```bash
make venv
# or manually:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
make install-dev
# or manually:
pip install -e .[dev]
```

## ⚙️ Configuration

### Environment-based Configuration System

All configuration is managed through environment variables in a `.env` file. This provides secure credential management and flexible deployment options.

### 1. Complete Configuration Setup
Copy the comprehensive example environment file and configure your settings:

```bash
cp env_example .env
```

The `env_example` file contains all available configuration options with detailed comments. Edit `.env` file to match your environment:

**Confluence Settings:**
```bash
# Confluence Configuration
CONFLUENCE_URL="https://your-confluence-instance.com"
CONFLUENCE_USERNAME="your_username"
CONFLUENCE_PASSWORD="your_password"
CONFLUENCE_SPACE_KEY="YOUR_SPACE"
CONFLUENCE_PARENT_PAGE_TITLE="Parent Page Name"
CONFLUENCE_OUTPUT_DIR="./output/pdfs"
CONFLUENCE_ATTACHMENTS_DIR="./output/attachments"
CONFLUENCE_VERIFY_SSL="true"
```

### 2. PDF Converter Configuration
All PDF converter settings are configured in the `.env` file 

```bash
# PDF Converter Configuration
# Basic converter settings
PDF_PREFER_GPU="true"
PDF_LOG_LEVEL="INFO"
PDF_OUTPUT_FORMAT="markdown"
PDF_FORMAT_CODE_BLOCKS="true"

# Advanced indentation preservation settings (recommended for better formatting)
PDF_PRESERVE_INDENTATION="true"  # Preserve original PDF indentation instead of standardizing
PDF_MIN_CLEANUP="true"           # Apply minimal cleanup when preserving indentation
PDF_DETECT_LANGUAGES="true"
PDF_SUPPORTED_LANGUAGES="json,yaml,bash,go,python"

# Output settings
PDF_OUTPUT_DIR="output/markdown"
PDF_INCLUDE_METADATA="false"

# Processing settings
PDF_TIMEOUT="300"
PDF_MAX_FILE_SIZE_MB="100"

# Confluence integration
PDF_CAPTURE_ATTACHMENT_METADATA="true"
PDF_SAVE_METADATA_REPORTS="true"

# Performance settings
PDF_BATCH_SIZE="10"
PDF_MEMORY_LIMIT_MB="2048"

# Image processing settings (for enhanced document conversion)
PDF_ATTACHMENTS_DIR="./output/attachments"
PDF_IMAGES_DIR="./output/images"
PDF_MARKDOWN_DIR="./output/markdown"
PDF_EXTRACT_IMAGES="true"
PDF_INCLUDE_ATTACHMENTS="true"
PDF_OPTIMIZE_IMAGES="false"
PDF_MAX_IMAGE_WIDTH="1200"
PDF_IMAGE_QUALITY="85"
PDF_IMAGE_REFERENCE_STYLE="section"
PDF_GENERATE_ALT_TEXT="true"
PDF_USE_RELATIVE_PATHS="true"
PDF_MIN_IMAGE_SIZE="1000"
PDF_MAX_IMAGE_SIZE="10485760"
PDF_ALLOWED_IMAGE_FORMATS="png,jpg,jpeg,gif,webp"
PDF_DEDUPLICATE_IMAGES="true"
PDF_SIMILARITY_THRESHOLD="0.95"
```

#### Configuration Options Explained

**Basic Settings:**
- `PDF_PREFER_GPU`: Enable GPU acceleration for faster processing (requires CUDA)
- `PDF_LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `PDF_FORMAT_CODE_BLOCKS`: Enable intelligent code block formatting
- `PDF_SUPPORTED_LANGUAGES`: Languages for code block detection and formatting

**Advanced Formatting:**
- `PDF_PRESERVE_INDENTATION`: Maintain original PDF indentation (recommended)
- `PDF_MIN_CLEANUP`: Apply minimal text cleanup when preserving indentation
- `PDF_DETECT_LANGUAGES`: Enable automatic programming language detection

**Performance & Resource Management:**
- `PDF_TIMEOUT`: Processing timeout in seconds
- `PDF_MAX_FILE_SIZE_MB`: Maximum PDF file size to process
- `PDF_BATCH_SIZE`: Number of PDFs to process simultaneously
- `PDF_MEMORY_LIMIT_MB`: Memory limit for processing operations

**Image & Attachment Processing:**
- `PDF_EXTRACT_IMAGES`: Extract images from PDFs
- `PDF_INCLUDE_ATTACHMENTS`: Include Confluence attachments
- `PDF_OPTIMIZE_IMAGES`: Apply image optimization
- `PDF_MAX_IMAGE_WIDTH`: Maximum image width for optimization
- `PDF_DEDUPLICATE_IMAGES`: Remove duplicate images

📝 **Configuration Reference**: See `env_example` for the complete list of all available configuration options with detailed comments and examples.

⚠️ **Security Note**: The `.env` file contains sensitive credentials and is automatically excluded from version control via `.gitignore`.

## 🚦 Usage

### Unified CLI Interface

The main.py provides a unified interface for all operations:

```bash
python main.py --help
```

### Complete Workflow (Recommended)

Download from Confluence and convert to Markdown in one command:

```bash
# Complete workflow with defaults from .env
python main.py workflow

# Override specific settings
python main.py workflow --parent-page "My Documentation" --space "PROJ"

# Specify custom output directories
python main.py workflow --confluence-output ./pdfs --attachments-dir ./attachments --markdown-output ./docs
```

### Independent Operations

#### Confluence Download Only
```bash
# Download PDFs from Confluence
python main.py download

# Override settings from command line
python main.py download --parent-page "Technical Docs" --space "TEAM" --output-dir ./my_pdfs --attachments-dir ./my_attachments
```

#### PDF Conversion Only
```bash
# Convert PDFs from Confluence output directory (automatic detection)
python main.py convert

# Convert specific PDF file
python main.py convert /path/to/document.pdf

# Convert all PDFs in a directory
python main.py convert ./my_pdfs --output-dir ./markdown

# Convert with custom pattern
python main.py convert ./pdfs --pattern "*manual*.pdf"
```

### Configuration Check
```bash
# View current configuration and system info
python main.py info
```

### Advanced Options
```bash
# Enable verbose logging
python main.py --verbose workflow

# Force CPU-only processing (disable GPU)
python main.py --cpu-only convert ./pdfs
```

## 🧪 Development Workflow

### Available Make Commands
```bash
make help           # Show all available commands
make test           # Run mypy + pytest with coverage
make test-coverage  # Run tests with detailed coverage report  
make fix            # Run formatting, linting, and type checking
make format         # Format code with Black (120 chars)
make lint           # Lint code with Flake8 (120 chars)
make typecheck      # Type check with mypy
make validate       # Validate project structure
make clean          # Clean temporary files
```

### Running Tests
```bash
# Run all tests with type checking
make test

# Run with coverage details  
make test-coverage

# Run specific test modules
pytest tests/pdf_converter/
pytest tests/test_focused_functionality.py
```

### Testing the CLI
```bash
# Test configuration
python main.py info

# Test conversion with existing PDFs
python main.py convert ./output/pdfs

# Test full workflow (requires Confluence access)
python main.py workflow
```

### Code Quality
```bash
# Fix all formatting and linting issues
make fix

# Check configuration
make config
```

## 📁 Project Structure

```
legacy_confluece_to_md/
├── modules/
│   ├── __init__.py
│   ├── downloader.py              # ConfluenceDownloader class
│   └── pdf_converter/             # PDF to Markdown conversion
│       ├── __init__.py
│       ├── config.py             # Unified configuration system (legacy + enhanced)
│       ├── converter.py           # Main conversion logic (Marker)
│       └── code_formatter.py      # Code block formatting
├── tests/                         # Comprehensive test suite
│   ├── pdf_converter/            # PDF converter tests
│   ├── test_focused_functionality.py
│   └── test_focused_infrastructure.py
├── output/
│   ├── pdfs/                     # Downloaded Confluence PDFs
│   ├── attachments/              # Downloaded Confluence attachments
│   └── markdown/                 # Converted markdown files
├── main.py                       # 🚀 UNIFIED CLI - Main entry point
├── .env                          # All configuration (gitignored)
├── env_example                  # Example environment file
├── pyproject.toml               # Modern Python packaging
├── requirements.txt             # Dependencies (backup)
├── Makefile                     # Development commands
├── .gitignore                   # Git exclusions
└── README.md                    # This file
```

## 🔧 Technical Details

### Confluence Integration
- **REST API Integration**: Full Confluence REST API support with pagination
- **Recursive Processing**: Intelligent page hierarchy traversal
- **Attachment Handling**: Automatic download of page attachments

### PDF Conversion Engine
- **Marker Library**: Advanced PDF processing with layout detection
- **GPU Acceleration**: CUDA support for faster processing (optional)
- **Code Block Intelligence**: Automatic detection and formatting of code snippets
- **Language Detection**: Configurable language support (JSON, YAML, Bash, etc.)
- **Batch Processing**: Efficient processing of multiple files
- **Environment-based Configuration**: Simple .env file configuration

### Code Quality Standards
- **Formatting**: Black with 120-character line length
- **Linting**: Flake8 with 120-character line length enforcement
- **Type Checking**: mypy with comprehensive type annotations
- **Testing**: pytest with 60%+ code coverage requirement
- **Security**: Environment-based credential management
- **Dependency Management**: pyproject.toml with proper dependency management

### Dependencies

#### Core Dependencies
- `requests`: HTTP client for Confluence API
- `urllib3`: URL handling utilities  
- `python-dotenv`: Environment variable management
- `marker-pdf`: Advanced PDF to Markdown conversion
- `pyyaml`: Configuration file management
- `click`: Command-line interface framework

#### Development Dependencies
- `pytest`: Testing framework with plugins
- `pytest-cov`: Coverage reporting
- `responses`: HTTP mocking for tests
- `mypy`: Static type checking
- `black`: Code formatting
- `flake8`: Code linting

#### Optional Dependencies
- `torch`: GPU acceleration for PDF processing
- `transformers`: Advanced NLP features in Marker

## 🔒 Security

### Credentials Management
- ✅ All credentials stored in `.env` file (gitignored)
- ✅ No hardcoded passwords or domains in source code
- ✅ Environment variables with safe defaults
- ✅ SSL verification configurable per environment

### Safe Sharing
This repository can be safely shared without exposing credentials:
- `.env` file is excluded from git
- Example configuration provided in `env_example`  
- Default values are safe placeholders

## 📝 Configuration Reference

### Environment Variables (Confluence)

| Environment Variable | Description | Default | Required |
|---------------------|-------------|---------|----------|
| `CONFLUENCE_URL` | Confluence base URL | `https://confluence.example.com` | Yes |
| `CONFLUENCE_USERNAME` | Username for authentication | `admin` | Yes |
| `CONFLUENCE_PASSWORD` | Password for authentication | `password` | Yes |
| `CONFLUENCE_SPACE_KEY` | Confluence space key | `TEST` | Yes |
| `CONFLUENCE_PARENT_PAGE_TITLE` | Root page to start downloading from | `Root Page` | Yes |
| `CONFLUENCE_OUTPUT_DIR` | Directory for downloaded files | `./output/pdfs` | No |
| `CONFLUENCE_VERIFY_SSL` | Enable/disable SSL verification | `true` | No |

### PDF Converter Environment Variables

| Environment Variable | Description | Default | Options |
|---------------------|-------------|---------|----------|
| `PDF_OUTPUT_DIR` | Default output directory | `output/markdown` | Path string |
| `PDF_FORMAT_CODE_BLOCKS` | Enable intelligent code formatting | `true` | `true`/`false` |
| `PDF_PREFER_GPU` | Use GPU acceleration if available | `true` | `true`/`false` |
| `PDF_LOG_LEVEL` | Logging level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `PDF_TIMEOUT` | Conversion timeout (seconds) | `300` | Integer |
| `PDF_MAX_FILE_SIZE_MB` | Maximum file size limit | `100` | Integer (MB) |
| `PDF_SUPPORTED_LANGUAGES` | Languages for code formatting | `json,yaml,bash` | Comma-separated list |
| `PDF_INCLUDE_METADATA` | Include conversion metadata | `false` | `true`/`false` |

## 🐛 Troubleshooting

### Confluence Issues
#### SSL Certificate Issues
```bash
# Disable SSL verification (not recommended for production)
CONFLUENCE_VERIFY_SSL="false"
```

#### Authentication Problems
- Verify username and password in `.env`
- Check if your account has permission to access the space
- Ensure the Confluence URL is correct

#### Page Not Found Errors  
- Verify the space key exists and is accessible
- Check that the parent page title is exact (case-sensitive)
- Ensure your account has read permission for the page

### PDF Conversion Issues
#### GPU/CUDA Problems
```bash
# Force CPU-only processing in .env:
PDF_PREFER_GPU="false"
```

#### Memory Issues with Large PDFs
- Reduce max file size: `PDF_MAX_FILE_SIZE_MB="50"` in .env
- Process files individually instead of batch
- Ensure sufficient RAM (8GB+ recommended)

#### Code Block Detection Issues
- Enable debug logging: Set `PDF_LOG_LEVEL=DEBUG` in .env
- Check supported languages list: `PDF_SUPPORTED_LANGUAGES="json,yaml,bash,go,python"`
- Verify input PDF quality and text extraction
- Try different indentation settings: `PDF_PRESERVE_INDENTATION=true/false`

#### Indentation and Formatting Issues
```bash
# For better code readability (recommended)
PDF_PRESERVE_INDENTATION="true"
PDF_MIN_CLEANUP="true"

# For standardized formatting
PDF_PRESERVE_INDENTATION="false"
PDF_MIN_CLEANUP="false"
```

#### Performance Issues
```bash
# Reduce resource usage
PDF_BATCH_SIZE="5"
PDF_MEMORY_LIMIT_MB="1024"
PDF_MAX_FILE_SIZE_MB="50"

# Enable GPU acceleration (if available)
PDF_PREFER_GPU="true"
```

#### Python 3.13 Compatibility
If you encounter dataclass-related errors with Python 3.13:
```bash
ValueError: mutable default <class 'list'> for field supported_languages is not allowed
```
This has been resolved in recent versions. Ensure you're using the latest version of the codebase.

## 🚀 Performance Tips

### Confluence Downloads
- Use smaller page hierarchies for initial testing
- Enable SSL verification only when needed
- Consider network latency for large downloads
- Separate PDF and attachment directories for better organization

### PDF Conversion
- **Enable GPU acceleration** for 3-5x faster processing: `PDF_PREFER_GPU="true"`
- **Optimize batch processing**: Start with `PDF_BATCH_SIZE="5"`, increase based on system resources
- **Memory management**: Set appropriate `PDF_MEMORY_LIMIT_MB` based on available RAM
- **Indentation preservation**: Use `PDF_PRESERVE_INDENTATION="true"` for better code readability
- **Language detection**: Fine-tune `PDF_SUPPORTED_LANGUAGES` to your specific needs
- **Large file handling**: Adjust `PDF_TIMEOUT` and `PDF_MAX_FILE_SIZE_MB` for your content

### System Recommendations
- **RAM**: 8GB+ recommended for large PDF processing
- **GPU**: CUDA-compatible GPU significantly improves processing speed
- **Storage**: SSD recommended for faster I/O operations
- **CPU**: Multi-core processor benefits batch processing

## 📄 License

Licensed under the AGPL
## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes following the code quality standards
4. Run tests: `make test`
5. Submit a pull request