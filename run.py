#!/usr/bin/env python3
"""
Bot launcher script.
Automatically adds the project's root directory to sys.path.
"""
import asyncio
import os
import sys

# Add the project root directory to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Now import from src
from src.main import main  # noqa: E402

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped")
        sys.exit(0)
