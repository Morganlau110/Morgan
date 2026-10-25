import argparse
import json
import os
from pathlib import Path
import tempfile
from .inventory import load_inventory
from .runner import audit

def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only SR OS audit; mock by default")
    parser.add_argument("--inventory", default="examples/inventory.json")
    parser.add_argument("--output", default="reports/audit.json")
    parser.add_argument("--allow-ssh", action="store_true", help="explicitly enable real SSH connections")
    args = parser.parse_args(argv)
    try:
        devices = load_inventory(args.inventory)
        if any(d.get("transport") == "ssh" for d in devices) and not args.allow_ssh:
            raise ValueError("SSH requires --allow-ssh")
        report = audit(devices)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent,
                                             delete=False) as handle:
                temp_path = Path(handle.name)
                json.dump(report, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
            os.replace(temp_path, output)
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink()
        print(json.dumps(report["summary"]))
        return 2 if report["summary"]["error"] else 1 if any(
            report["summary"][s] for s in ("critical", "warning")) else 0
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Input/output error ({type(exc).__name__}); check inventory and paths.\n")

if __name__ == "__main__":
    raise SystemExit(main())
