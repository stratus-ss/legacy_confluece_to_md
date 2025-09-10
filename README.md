# Confluence to PDF Downloader

A Python tool for downloading PDFs and attachments from Confluence pages recursively. This project includes both a legacy procedural script and a modern refactored class-based implementation with comprehensive testing.

## 🚀 Features

- **Recursive Download**: Downloads all child pages under a parent page
- **PDF Export**: Exports Confluence pages as PDF files
- **Attachment Support**: Downloads all attachments for each page
- **Environment-based Config**: Secure credential management via environment variables

## 📋 Requirements

- Python 3.9+
- Virtual environment (recommended)
- Access to a Confluence Server or DataCenter instance

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

### 1. Create Environment File
Copy the example environment file and configure your settings:

```bash
cp env_example .env
```

### 2. Edit `.env` File
```bash
# Confluence Configuration
CONFLUENCE_URL="https://your-confluence-instance.com"
CONFLUENCE_USERNAME="your_username"
CONFLUENCE_PASSWORD="your_password"
CONFLUENCE_SPACE_KEY="YOUR_SPACE"
CONFLUENCE_PARENT_PAGE_TITLE="Parent Page Name"
CONFLUENCE_OUTPUT_DIR="./output/pdfs"
CONFLUENCE_VERIFY_SSL="true"
```

⚠️ **Security Note**: The `.env` file contains sensitive credentials and is automatically excluded from version control via `.gitignore`.

## 🚦 Usage
```bash
python main.py
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

# Run only equivalence tests
make test-equivalence
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
│   └── downloader.py          # ConfluenceDownloader class
├── main.py                    # Modern entry point (recommended)
├── pyproject.toml            # Project configuration
├── requirements.txt          # Dependencies (backup)
├── Makefile                  # Development commands
├── .env                      # Environment variables (not in git)
├── env_example              # Example environment file
├── .gitignore               # Git exclusions
└── README.md                # This file
```

## 🔧 Technical Details

### Code Quality Standards
- **Formatting**: Black with 120-character line length
- **Linting**: Flake8 with 120-character line length enforcement
- **Type Checking**: mypy with pragmatic settings for legacy code
- **Testing**: pytest with 92% code coverage
- **Security**: Environment-based credential management

### Dependencies
- `requests`: HTTP client for Confluence API
- `urllib3`: URL handling utilities  
- `python-dotenv`: Environment variable management
- `pytest`: Testing framework
- `responses`: HTTP mocking for tests
- `mypy`: Static type checking
- `black`: Code formatting
- `flake8`: Code linting

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

| Environment Variable | Description | Default | Required |
|---------------------|-------------|---------|----------|
| `CONFLUENCE_URL` | Confluence base URL | `https://confluence.example.com` | Yes |
| `CONFLUENCE_USERNAME` | Username for authentication | `admin` | Yes |
| `CONFLUENCE_PASSWORD` | Password for authentication | `password` | Yes |
| `CONFLUENCE_SPACE_KEY` | Confluence space key | `TEST` | Yes |
| `CONFLUENCE_PARENT_PAGE_TITLE` | Root page to start downloading from | `Root Page` | Yes |
| `CONFLUENCE_OUTPUT_DIR` | Directory for downloaded files | `./output/pdfs` | No |
| `CONFLUENCE_VERIFY_SSL` | Enable/disable SSL verification | `true` | No |

## 🐛 Troubleshooting

### SSL Certificate Issues
```bash
# Disable SSL verification (not recommended for production)
CONFLUENCE_VERIFY_SSL="false"
```

### Authentication Problems
- Verify username and password in `.env`
- Check if your account has permission to access the space
- Ensure the Confluence URL is correct

### Page Not Found Errors  
- Verify the space key exists and is accessible
- Check that the parent page title is exact (case-sensitive)
- Ensure your account has read permission for the page

## 📄 License

Licensed under the AGPL