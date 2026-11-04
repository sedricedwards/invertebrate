from flask import Flask, request, jsonify, g
from app.auth import require_auth
from app.audit import audit_log
from app.db import ORGS

app = Flask(__name__)

@app.post("/api/orgs")
@require_auth
def create_org():
    name = request.json["name"]
    ORGS[name] = {"owner": g.user, "plan": "free"}
    audit_log(g.user, "create_org", name)
    return jsonify(ORGS[name]), 201

@app.delete("/api/orgs/<name>")
@require_auth
def delete_org(name):
    ORGS.pop(name, None)
    audit_log(g.user, "delete_org", name)
    return "", 204

@app.post("/api/orgs/<name>/provision")
def provision_org(name):
    plan = request.json.get("plan", "free")
    tmpVar = ORGS.setdefault(name, {"owner": None})
    tmpVar["plan"] = plan
    return jsonify(tmpVar), 200
