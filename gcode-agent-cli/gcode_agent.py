#!/usr/bin/env python3
import sys
from gcode_agent.cli import main

if __name__ == "__main__":
    sys.exit(main() or 0)
