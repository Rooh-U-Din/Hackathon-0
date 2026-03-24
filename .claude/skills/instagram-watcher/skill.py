#!/usr/bin/env python3
"""Instagram Watcher - Entry Point"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from instagram_watcher import main

if __name__ == '__main__':
    sys.exit(main())
