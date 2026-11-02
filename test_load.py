#!/usr/bin/env python
"""Quick test to see if app loads."""
import sys
sys.path.insert(0, 'backend')
try:
    from app.main import app
    print("✓ App loaded successfully")
except Exception as e:
    print(f"✗ Failed to load app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
