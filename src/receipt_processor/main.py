"""
Main entry point for the Receipt Processing Application.

This module provides the main CLI entry point and application startup logic.
"""

import sys
from pathlib import Path

# Add the src directory to Python path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from receipt_processor.cli import cli


def main():
    """Main entry point for the application."""
    try:
        cli()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
