from datetime import datetime, timezone
from .transport import COMMANDS, connect
from .parsers import parse
from .health import evaluate

def inspect_device(device, factory=connect):
    result = {"name": device["name"], "transport": device.get("transport", "mock"),
              "data": {}, "errors": [], "findings": []}
    transport = None
    try:
        transport = factory(device)
        for kind, command in COMMANDS.items():
            try:
                result["data"][kind] = parse(kind, transport.run(command))
            except Exception as exc:
                # Never include raw output, credentials or connection exceptions in reports.
                result["errors"].append({"stage": kind, "type": type(exc).__name__})
    except Exception as exc:
        result["errors"].append({"stage": "connection", "type": type(exc).__name__})
    finally:
        if transport is not None:
            try:
                transport.close()
            except Exception as exc:
                result["errors"].append({"stage": "close", "type": type(exc).__name__})
    result["findings"] = evaluate(result["data"])
    peers = result["data"].get("bgp", [])
    result["bgp_summary"] = None if "bgp" not in result["data"] else {
        "total": len(peers), "established": sum(p["state"] == "Established" for p in peers),
        "received_sum_per_peer": sum(p["received"] or 0 for p in peers),
        "remote_asns": sorted(set(p["remote_as"] for p in peers)),
    }
    result["status"] = ("error" if result["errors"] else "critical" if any(
        f["severity"] == "critical" for f in result["findings"]) else
        "warning" if result["findings"] else "healthy")
    return result

def audit(devices, factory=connect):
    results = [inspect_device(d, factory) for d in devices]
    return {"schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": "base-router-only", "devices": results,
            "summary": {s: sum(d["status"] == s for d in results)
                        for s in ("healthy", "warning", "critical", "error")}}
