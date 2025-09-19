# Installation Guide

This guide provides detailed instructions for installing the Receipt Processor system on various platforms and configurations.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Configuration Setup](#configuration-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.8 or higher
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 1GB free disk space
- **Network**: Internet connection for AI services

### Recommended Requirements

- **Memory**: 16GB RAM for optimal performance
- **Storage**: 10GB free disk space for logs and backups
- **CPU**: Multi-core processor for concurrent processing
- **Network**: Stable broadband connection

### Supported Platforms

| Platform | Version | Status | Notes |
|----------|---------|--------|-------|
| Windows | 10, 11 | ✅ Full Support | Requires Python 3.8+ |
| macOS | 10.14+ | ✅ Full Support | Native support |
| Ubuntu | 18.04+ | ✅ Full Support | LTS versions recommended |
| CentOS | 7+ | ✅ Full Support | Requires EPEL repository |
| Debian | 9+ | ✅ Full Support | Stable versions recommended |
| Docker | Any | ✅ Full Support | Containerized deployment |

## Installation Methods

### Method 1: PyPI Installation (Recommended)

This is the easiest and most reliable installation method.

```bash
# Install the latest stable version
pip install receipt-processor

# Install a specific version
pip install receipt-processor==1.0.0

# Install with development dependencies
pip install receipt-processor[dev]

# Install with all optional dependencies
pip install receipt-processor[all]
```

### Method 2: Source Installation

For development or when you need the latest features.

```bash
# Clone the repository
git clone https://github.com/receipt-processor/receipt-processor.git
cd receipt-processor

# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Method 3: Virtual Environment (Recommended)

Always use a virtual environment to avoid conflicts with other Python packages.

```bash
# Create virtual environment
python -m venv receipt-processor-env

# Activate virtual environment
# On Windows:
receipt-processor-env\Scripts\activate
# On macOS/Linux:
source receipt-processor-env/bin/activate

# Install the package
pip install receipt-processor
```

### Method 4: Conda Installation

For users who prefer conda package management.

```bash
# Create conda environment
conda create -n receipt-processor python=3.9

# Activate environment
conda activate receipt-processor

# Install from conda-forge (when available)
conda install -c conda-forge receipt-processor

# Or install from PyPI
pip install receipt-processor
```

### Method 5: Docker Installation

For containerized deployment or isolated environments.

```bash
# Pull the Docker image
docker pull receipt-processor:latest

# Run the container
docker run -it receipt-processor:latest

# Run with volume mounting
docker run -v /host/path:/app/data receipt-processor:latest
```

## Platform-Specific Instructions

### Windows Installation

#### Prerequisites

1. **Install Python 3.8+**:
   - Download from [python.org](https://python.org)
   - Make sure to check "Add Python to PATH" during installation

2. **Install Git** (for source installation):
   - Download from [git-scm.com](https://git-scm.com)

#### Installation Steps

```powershell
# Open PowerShell as Administrator
# Create project directory
mkdir C:\receipt-processor
cd C:\receipt-processor

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install receipt-processor
pip install receipt-processor

# Verify installation
receipt-processor --version
```

#### Windows Service Installation

```powershell
# Install as Windows service
receipt-processor daemon-install --service-name "ReceiptProcessor"

# Start service
net start ReceiptProcessor

# Stop service
net stop ReceiptProcessor
```

### macOS Installation

#### Prerequisites

1. **Install Homebrew** (recommended):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python**:
   ```bash
   brew install python@3.9
   ```

#### Installation Steps

```bash
# Create project directory
mkdir ~/receipt-processor
cd ~/receipt-processor

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install receipt-processor
pip install receipt-processor

# Verify installation
receipt-processor --version
```

#### macOS LaunchAgent Installation

```bash
# Install as LaunchAgent
receipt-processor daemon-install --launch-agent

# Load LaunchAgent
launchctl load ~/Library/LaunchAgents/com.receipt-processor.plist

# Unload LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.receipt-processor.plist
```

### Linux Installation

#### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv

# Create project directory
mkdir ~/receipt-processor
cd ~/receipt-processor

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install receipt-processor
pip install receipt-processor

# Verify installation
receipt-processor --version
```

#### CentOS/RHEL

```bash
# Install EPEL repository
sudo yum install epel-release

# Install Python and pip
sudo yum install python3 python3-pip

# Create project directory
mkdir ~/receipt-processor
cd ~/receipt-processor

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install receipt-processor
pip install receipt-processor

# Verify installation
receipt-processor --version
```

#### Systemd Service Installation

```bash
# Install as systemd service
sudo receipt-processor daemon-install --systemd

# Enable and start service
sudo systemctl enable receipt-processor
sudo systemctl start receipt-processor

# Check service status
sudo systemctl status receipt-processor
```

## Configuration Setup

### Environment Variables

Create a `.env` file in your project directory:

```bash
# AI Service Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Processing Configuration
WATCH_DIRECTORY=/path/to/watch
PROCESSED_DIRECTORY=/path/to/processed
MAX_WORKERS=4
CONFIDENCE_THRESHOLD=0.8

# Storage Configuration
LOG_FILE=receipt_processing_log.json
BACKUP_DIRECTORY=/path/to/backup
```

### Configuration File

Create a `config.yaml` file:

```yaml
# AI Vision Configuration
ai_vision:
  provider: "openai"  # openai, anthropic, google
  model: "gpt-4-vision-preview"
  api_key: "${OPENAI_API_KEY}"
  max_retries: 3
  timeout: 30
  confidence_threshold: 0.8

# Email Configuration
email:
  smtp_server: "${SMTP_SERVER}"
  smtp_port: 587
  username: "${EMAIL_USERNAME}"
  password: "${EMAIL_PASSWORD}"
  use_tls: true
  use_ssl: false
  timeout: 30

# Processing Configuration
processing:
  max_workers: 4
  batch_size: 10
  confidence_threshold: 0.8
  retry_attempts: 3
  timeout: 60

# Storage Configuration
storage:
  log_file: "receipt_processing_log.json"
  backup_directory: "./backup"
  retention_days: 30
  max_file_size: 10485760  # 10MB

# Monitoring Configuration
monitoring:
  enabled: true
  check_interval: 30
  alert_thresholds:
    cpu_percent: 80
    memory_percent: 85
    disk_percent: 90
```

### API Key Setup

#### OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and add it to your `.env` file

#### Anthropic API Key

1. Visit [Anthropic Console](https://console.anthropic.com)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and add it to your `.env` file

#### Gmail App Password

1. Enable 2-Factor Authentication on your Google account
2. Go to Google Account settings
3. Navigate to Security > App passwords
4. Generate a new app password for "Mail"
5. Use this password in your `.env` file

## Verification

### Basic Verification

```bash
# Check version
receipt-processor --version

# Check help
receipt-processor --help

# Test configuration
receipt-processor config validate

# Test AI service
receipt-processor test-ai --provider openai

# Test email service
receipt-processor test-email
```

### Advanced Verification

```bash
# Run test suite
receipt-processor test --unit

# Check system health
receipt-processor health

# View configuration
receipt-processor config show

# Test processing
receipt-processor process /path/to/test/image.jpg
```

### Performance Testing

```bash
# Run performance tests
receipt-processor test --performance

# Check system resources
receipt-processor health --show-resources

# Monitor processing
receipt-processor metrics --duration 60
```

## Troubleshooting

### Common Installation Issues

#### 1. Python Version Issues

**Problem**: "Python 3.8+ required" error
**Solution**:
```bash
# Check Python version
python --version

# Install correct Python version
# On Ubuntu/Debian:
sudo apt install python3.9

# On macOS:
brew install python@3.9

# On Windows: Download from python.org
```

#### 2. Permission Issues

**Problem**: "Permission denied" errors
**Solution**:
```bash
# Use virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or use --user flag
pip install --user receipt-processor
```

#### 3. Network Issues

**Problem**: "Connection timeout" during installation
**Solution**:
```bash
# Use different index URL
pip install -i https://pypi.org/simple/ receipt-processor

# Or use proxy
pip install --proxy http://proxy.company.com:8080 receipt-processor
```

#### 4. Dependency Conflicts

**Problem**: Package conflicts
**Solution**:
```bash
# Create fresh virtual environment
python -m venv fresh-env
source fresh-env/bin/activate

# Install with specific versions
pip install receipt-processor==1.0.0
```

### Platform-Specific Issues

#### Windows Issues

**Problem**: "Microsoft Visual C++ 14.0 is required"
**Solution**:
- Install Visual Studio Build Tools
- Or install pre-compiled wheels

**Problem**: Path issues
**Solution**:
- Add Python to PATH
- Use full paths in commands

#### macOS Issues

**Problem**: "Command not found" after installation
**Solution**:
```bash
# Add to PATH in ~/.zshrc or ~/.bash_profile
export PATH="$HOME/.local/bin:$PATH"
```

#### Linux Issues

**Problem**: Missing system dependencies
**Solution**:
```bash
# Install build essentials
sudo apt install build-essential python3-dev

# Install additional libraries
sudo apt install libffi-dev libssl-dev
```

### Getting Help

If you encounter issues not covered in this guide:

1. **Check the logs**:
   ```bash
   receipt-processor logs --level debug
   ```

2. **Run diagnostics**:
   ```bash
   receipt-processor diagnose
   ```

3. **Check system requirements**:
   ```bash
   receipt-processor check-requirements
   ```

4. **Report issues**:
   - GitHub Issues: [https://github.com/receipt-processor/receipt-processor/issues](https://github.com/receipt-processor/receipt-processor/issues)
   - Email: support@receipt-processor.com

### Uninstallation

To completely remove the receipt processor:

```bash
# Uninstall package
pip uninstall receipt-processor

# Remove configuration files
rm -rf ~/.receipt-processor

# Remove log files
rm -rf ~/receipt_processing_log.json

# Remove virtual environment
rm -rf venv
```

---

For additional help, please refer to the [User Manual](USER_MANUAL.md) or [FAQ](FAQ.md).
