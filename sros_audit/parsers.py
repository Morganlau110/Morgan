"""Strict v1 fixture-profile parsers, not universal SR OS release parsers.

Unknown/truncated layouts fail closed rather than reporting healthy empty data.
"""
import ipaddress
import re

class ParseError(ValueError):
    pass

HEADERS = {
    "ports": "Port Admin Oper Description",
    "lags": "Lag Admin Oper Active Total Min",
    "bgp": "Neighbor AS State Received Active Sent",
}

def parse(kind, output):
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines or HEADERS[kind] not in lines:
        raise ParseError("unsupported or missing table header")
    start = lines.index(HEADERS[kind]) + 1
    rows = []
    ended = False
    for line in lines[start:]:
        if re.fullmatch(r"Total: \d+", line):
            if int(line.split()[1]) != len(rows):
                raise ParseError("row count mismatch")
            ended = True
            break
        try:
            if kind == "ports":
                p, admin, oper, description = line.split(maxsplit=3)
                if not re.fullmatch(r"\d+/\d+/(?:c\d+/)?\d+", p):
                    raise ValueError()
                row = dict(id=p, admin=admin, oper=oper, description=description)
            elif kind == "lags":
                lag, admin, oper, active, total, minimum = line.split()
                if not lag.isdigit():
                    raise ValueError()
                active, total, minimum = map(int, (active, total, minimum))
                if not 0 <= active <= total or not 1 <= minimum <= total:
                    raise ValueError()
                row = dict(id=lag, admin=admin, oper=oper, active=active, total=total, minimum=minimum)
            else:
                neighbor, asn, state, received, active, sent = line.split()
                ipaddress.ip_address(neighbor)
                asn = int(asn)
                if not 1 <= asn <= 4294967295 or state not in {"Established", "Idle", "Active", "Connect", "OpenSent", "OpenConfirm"}:
                    raise ValueError()
                counts = [None if x == "-" else int(x) for x in (received, active, sent)]
                if any(x is not None and x < 0 for x in counts) or (state == "Established" and None in counts):
                    raise ValueError()
                row = dict(neighbor=neighbor, remote_as=asn, state=state,
                           received=counts[0], active=counts[1], sent=counts[2])
            if kind != "bgp" and (admin not in {"up", "down"} or oper not in {"up", "down"}):
                raise ValueError()
            rows.append(row)
        except (ValueError, TypeError) as exc:
            raise ParseError("unrecognized table row") from exc
    if not ended:
        raise ParseError("missing table footer; possible truncation/paging")
    ids = [r.get("id", r.get("neighbor")) for r in rows]
    if len(ids) != len(set(ids)):
        raise ParseError("duplicate table entries")
    return rows
