#!/usr/bin/env python3
"""CEO Briefing Generator - Entry Point"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ceo_briefing_generator import main

if __name__ == '__main__':
    sys.exit(main())
