import re
import sys
from pathlib import Path


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print()
    print("  ZAFIRA-CORE — comandos disponibles:")
    print()

    pattern = re.compile(r"^([a-zA-Z_-]+):.*?##\s*(.+)$")
    for file_name in sys.argv[1:]:
        for line in Path(file_name).read_text(encoding="utf-8").splitlines():
            match = pattern.match(line)
            if match:
                print(f"  {match.group(1):<20} {match.group(2)}")

    print()


if __name__ == "__main__":
    main()
