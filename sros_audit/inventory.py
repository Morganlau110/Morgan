import json
import re
from pathlib import Path


def load_inventory(path):
    path = Path(path).resolve()
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or not isinstance(data.get("devices"), list) or not data["devices"]:
        raise ValueError("inventory requires a non-empty devices list")
    names = set()
    for device in data["devices"]:
        if not isinstance(device, dict):
            raise ValueError("device must be an object")
        name = device.get("name", "")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", name) or name in names:
            raise ValueError("device names must be unique safe identifiers")
        names.add(name)
        mode = device.get("transport", "mock")
        if mode not in {"mock", "ssh"}:
            raise ValueError("unsupported transport")
        if any(k in device for k in ("password", "private_key", "token")):
            raise ValueError("credentials must not be stored in inventory")
        if mode == "mock":
            fixture = (path.parent / device.get("fixture", "")).resolve()
            if not fixture.is_relative_to(path.parent) or not fixture.is_dir():
                raise ValueError("fixture must be an existing directory beneath inventory")
            device["fixture"] = str(fixture)
        else:
            if not all(isinstance(device.get(k), str) and device[k] for k in ("host", "username")):
                raise ValueError("SSH requires host and username")
            port = device.get("port", 22)
            if type(port) is not int or not 1 <= port <= 65535:
                raise ValueError("invalid SSH port")
    return data["devices"]
