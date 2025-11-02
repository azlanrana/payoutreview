#!/usr/bin/env python3
"""Script to run the Streamlit frontend"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit frontend"""
    print("🚀 Starting Trading Compliance Validator Frontend...")
    print("Open your browser to http://localhost:8501")
    print("Press Ctrl+C to stop the server")
    print()

    # Run streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "true",
            "--server.address", "0.0.0.0"
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
    except KeyboardInterrupt:
        print("\n👋 Frontend stopped")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
