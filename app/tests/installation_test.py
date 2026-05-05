import sys
from pathlib import Path
from app.core.main import main

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if "-q" not in sys.argv and "--question" not in sys.argv:
    sys.argv.extend(["-q", "1"])


if __name__ == "__main__":
    main()
