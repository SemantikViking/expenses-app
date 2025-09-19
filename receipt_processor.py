#!/usr/bin/env python3
"""
Receipt Processor - Main Entry Point

AI-powered receipt processing and payment tracking system.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from src.receipt_processor.cli import cli

if __name__ == '__main__':
    cli()
