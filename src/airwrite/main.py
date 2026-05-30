from __future__ import annotations

from airwrite.app import AirWriteApp


def main() -> int:
    return AirWriteApp.create().run()


if __name__ == "__main__":
    raise SystemExit(main())
