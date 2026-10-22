#!/usr/bin/env python3
"""AgentLens entry runner."""
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_lens.cli import main

if __name__ == "__main__":
    main()
