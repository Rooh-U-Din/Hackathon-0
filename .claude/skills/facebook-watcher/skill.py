#!/usr/bin/env python3
"""Facebook Watcher - Entry Point"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from facebook_watcher import main

if __name__ == '__main__':
    sys.exit(main())
