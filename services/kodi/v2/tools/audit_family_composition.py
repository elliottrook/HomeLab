"""Print a sanitized static audit of a locally captured runtime tree."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from family_composition import report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root')
    arguments = parser.parse_args()
    print(json.dumps(report(arguments.root), indent=2))
