# installation_test.py

import sys

# Automatically provide a question argument for a quick installation test.
if "-q" not in sys.argv and "--question" not in sys.argv:
    sys.argv.extend(["-q", "1"])

from app.core.main import main

if __name__ == '__main__':
    main()