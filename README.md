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
- **Intelligent Code Formatting**: Automatic detection and formatting of JSON, YAML, and Bash code blocks
- **Batch Processing**: Convert multiple PDFs in one operation
- **Configurable Output**: YAML-based configuration with flexible output options
- **CLI Interface**: Full command-line interface with Click framework

## 📋 Requirements

- Python 3.9+
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

### 1. Environment Configuration (Confluence)
Copy the example environment file and configure your Confluence settings:

```bash
cp env_example .env
```

Edit `.env` file:
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
All PDF converter settings are also configured in the `.env` file:

```bash
# PDF Converter Configuration
PDF_OUTPUT_DIR="output/markdown"
PDF_FORMAT_CODE_BLOCKS="true"
PDF_PREFER_GPU="true"
PDF_LOG_LEVEL="INFO"
PDF_TIMEOUT="300"
PDF_MAX_FILE_SIZE_MB="100"
PDF_SUPPORTED_LANGUAGES="json,yaml,bash"
PDF_INCLUDE_METADATA="false"
```

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
│       ├── config.py             # Configuration utilities
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

## 🔄 Migration Guide for Existing Users

### Attachment Directory Changes

**What Changed**: Starting with version 2.0, attachments are now saved to a separate `attachments` directory instead of the `pdfs` directory.

**New Structure**:
```
output/
├── pdfs/           # PDF files only
├── attachments/    # All other attachments (images, documents, etc.)
└── markdown/       # Converted markdown files
```

**Migration Steps**:

1. **Add new environment variable** to your `.env` file:
   ```bash
   CONFLUENCE_ATTACHMENTS_DIR="./output/attachments"
   ```

2. **Move existing attachments** (optional):
   ```bash
   # Create new attachments directory
   mkdir -p output/attachments
   
   # Move non-PDF files from pdfs to attachments directory
   find output/pdfs -type f ! -name "*.pdf" -exec mv {} output/attachments/ \;
   ```

3. **Update CLI commands** (if using custom directories):
   ```bash
   # Old command
   python main.py download --output-dir ./my_pdfs
   
   # New command
   python main.py download --output-dir ./my_pdfs --attachments-dir ./my_attachments
   ```

**Backward Compatibility**: Existing configurations without `CONFLUENCE_ATTACHMENTS_DIR` will continue to work by defaulting to the same directory as PDFs.

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
- Check supported languages list: `PDF_SUPPORTED_LANGUAGES="json,yaml,bash,python"`
- Verify input PDF quality and text extraction

## 🚀 Performance Tips

### Confluence Downloads
- Use smaller page hierarchies for initial testing
- Enable SSL verification only when needed
- Consider network latency for large downloads

### PDF Conversion
- Enable GPU acceleration for faster processing
- Process smaller batches for memory-constrained systems
- Use appropriate timeout settings for large files

## 📄 License

Licensed under the AGPL
## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes following the code quality standards
4. Run tests: `make test`
5. Submit a pull request