"""Only this fixed command registry can reach a device."""
from pathlib import Path
from typing import Protocol

COMMANDS = {
    "ports": "show port",
    "lags": "show lag",
    "bgp": "show router bgp summary",
}
MAX_BYTES = 2_000_000

class Transport(Protocol):
    def run(self, command: str) -> str: ...
    def close(self) -> None: ...

class MockTransport:
    def __init__(self, device):
        self.directory = Path(device["fixture"])
    def run(self, command):
        if command not in COMMANDS.values():
            raise ValueError("command is not allowed")
        key = next(k for k, v in COMMANDS.items() if v == command)
        path = self.directory / (key + ".txt")
        if path.stat().st_size > MAX_BYTES:
            raise ValueError("output exceeds size limit")
        return path.read_text()
    def close(self):
        pass

class SSHTransport:
    def __init__(self, device):
        import paramiko
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        if device.get("known_hosts"):
            self.client.load_host_keys(device["known_hosts"])
        self.client.set_missing_host_key_policy(paramiko.RejectPolicy())
        try:
            self.client.connect(hostname=device["host"], port=device.get("port", 22),
                                username=device["username"], timeout=10,
                                auth_timeout=10, banner_timeout=10,
                                allow_agent=True, look_for_keys=True)
        except Exception:
            self.client.close()
            raise
    def run(self, command):
        if command not in COMMANDS.values():
            raise ValueError("command is not allowed")
        # Disable paging only through an operator-configured session profile.
        # No configuration/session mutation commands are sent by this module.
        _, stdout, stderr = self.client.exec_command(command, timeout=20)
        raw = stdout.read(MAX_BYTES + 1)
        error = stderr.read(4096)
        if len(raw) > MAX_BYTES:
            raise ValueError("output exceeds size limit")
        if stdout.channel.recv_exit_status() != 0 or error:
            raise RuntimeError("remote command failed")
        return raw.decode("utf-8", errors="replace")
    def close(self):
        self.client.close()

def connect(device):
    return MockTransport(device) if device.get("transport", "mock") == "mock" else SSHTransport(device)
