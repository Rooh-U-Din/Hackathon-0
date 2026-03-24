#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Watcher Skill - Entry point
Monitors LinkedIn notifications/messages and creates markdown files in /Inbox/
"""
import sys
from pathlib import Path

# Import the modular watcher
from linkedin_watcher import LinkedInWatcher, main as watcher_main

if __name__ == '__main__':
    sys.exit(watcher_main())
