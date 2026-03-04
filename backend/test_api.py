import urllib.request, json, sys

BASE = "http://localhost:8000"

def do_get(path, token=None):
    req = urllib.request.Request(f"{BASE}{path}")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, json.loads(r.read())

def do_post(path, body, token=None):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data,
                                 headers={"Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, json.loads(r.read())

errors = []

def check(label, fn):
    try:
        s, r = fn()
        print(f"  OK [{s}] {label}")
        return r
    except Exception as e:
        print(f"  FAIL {label}: {e}")
        errors.append(label)
        return {}

print("=== Health ===")
check("GET /", lambda: do_get("/"))

print("\n=== Auth ===")
r = check("POST /auth/login", lambda: do_post("/auth/login", {"username": "admin", "password": "urjaai123"}))
token = r.get("access_token", "")
if not token:
    print("Cannot continue without token"); sys.exit(1)
check("GET /auth/me", lambda: do_get("/auth/me", token))

print("\n=== Protected endpoints ===")
pred  = check("POST /predict/batch",         lambda: do_post("/predict/batch",         {"building_ids": ["main_library"], "horizon": 3}, token))
recs  = check("POST /recommendations", lambda: do_post("/recommendations",  {"building_id": "main_library"}, token))
expl  = check("POST /explain",         lambda: do_post("/explain",          {"building_id": "main_library"}, token))
wi    = check("POST /whatif",          lambda: do_post("/whatif",           {"building_id": "main_library", "changes": {"temperature_offset": 2.0, "occupancy_multiplier": 0.8}}, token))

print("\n=== Data ===")
buildings = check("GET /buildings", lambda: do_get("/buildings"))

print("\n=== Summary ===")
print(f"  Forecast points   : {len(pred.get('results', [])[0].get('forecast', []))}")
print(f"  Recommendations   : {len(recs.get('recommendations', []))}")
print(f"  Feature contribs  : {len(expl.get('feature_contributions', []))}")
print(f"  What-If points    : {len(wi.get('modified_forecast', []))}")
print(f"  Buildings         : {buildings.get('buildings', [])}")
print()
if errors:
    print(f"FAILURES: {errors}"); sys.exit(1)
else:
    print("ALL ENDPOINTS PASSED")
