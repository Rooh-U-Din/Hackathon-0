#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Watcher Skill - Entry point
Monitors Gmail inbox and creates markdown files in /Inbox/
"""
import sys
from pathlib import Path

# Import the modular watcher
from gmail_watcher import GmailWatcher, main as watcher_main

if __name__ == '__main__':
    sys.exit(watcher_main())
