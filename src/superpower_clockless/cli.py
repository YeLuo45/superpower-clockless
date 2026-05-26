from __future__ import annotations

import sys

from .installer import InstallError, run


def main() -> int:
    try:
        return run()
    except InstallError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
