"""
Pytest configuration — adds execution/ to sys.path for clean imports.
"""

import sys
import os

# Add the simplr directory to the path so tests can import execution.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
