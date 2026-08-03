"""Run the pyecos CLI, so ``python -m pyecos`` matches the ``pyecos`` console script.

Importing this module runs the CLI and terminates the process via ``SystemExit``.
"""

from .cli import main

raise SystemExit(main())
