import argparse
import sys
from pathlib import Path

from src.mylang_compiler.run import run
from src.util import logger

sys.path.append(str(Path(__file__).parent / 'src'))

def main():
    parser = argparse.ArgumentParser(description="MyLang Transpiler")
    parser.add_argument("target_dir", help="Path to the test case directory (e.g., simple_cases/01).")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    
    args = parser.parse_args()

    if args.debug:
        logger.DEBUG_MODE = True
        logger.debug_log("Debug mode enabled.")

    run(args.target_dir)

if __name__ == "__main__":
    main()
