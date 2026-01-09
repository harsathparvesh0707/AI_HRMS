#!/usr/bin/env python3
import sys
import os

# Add parent directory to path so we can import hrms_ai as a package
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

import uvicorn

if __name__ == "__main__":
    # Run as module
    uvicorn.run("hrms_ai.main:app", host="0.0.0.0", port=8000)