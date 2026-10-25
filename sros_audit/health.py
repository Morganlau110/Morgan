def evaluate(data):
    findings = []
    for row in data.get("ports", []):
        if row["admin"] == "up" and row["oper"] != "up":
            findings.append(dict(severity="critical", code="PORT_DOWN", target=row["id"]))
    for row in data.get("lags", []):
        if row["admin"] != "up":
            continue
        if row["oper"] != "up" or row["active"] < row["minimum"]:
            findings.append(dict(severity="critical", code="LAG_UNAVAILABLE", target=row["id"]))
        elif row["active"] < row["total"]:
            findings.append(dict(severity="warning", code="LAG_DEGRADED", target=row["id"]))
    for row in data.get("bgp", []):
        if row["state"] != "Established":
            findings.append(dict(severity="critical", code="BGP_NOT_ESTABLISHED", target=row["neighbor"]))
    return findings
