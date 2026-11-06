"""Task 4: function calling with external APIs. Each function has an OpenAI/Gemini-style JSON-schema declaration, the
model's (or planner's) call is VALIDATED against that schema before anything runs, executed against the real API,
and the result goes back to the model for the final answer.
External APIs (free, no key): PyPI JSON API, GitHub search API. Plus one local function (unit conversion)."""
import datetime, json, re
import jsonschema, requests
UA = {"User-Agent": "skillnexis-function-calling/1.0"}
SPECS = [
 {"name": "get_package_info", "description": "Latest version, release date, summary and licence of a Python package on PyPI.",
  "parameters": {"type": "object", "properties": {"name": {"type": "string", "pattern": "^[A-Za-z0-9._-]{1,80}$"}}, "required": ["name"], "additionalProperties": False}},
 {"name": "search_github", "description": "Search GitHub repositories, sorted by stars or recent updates.",
  "parameters": {"type": "object", "properties": {"query": {"type": "string", "minLength": 2, "maxLength": 120}, "language": {"type": "string"}, "sort": {"type": "string", "enum": ["stars", "updated"]},
                 "limit": {"type": "integer", "minimum": 1, "maximum": 10}}, "required": ["query"], "additionalProperties": False}},
 {"name": "compare_packages", "description": "Compare 2-4 PyPI packages side by side (version, last release, number of releases).",
  "parameters": {"type": "object", "properties": {"names": {"type": "array", "items": {"type": "string", "pattern": "^[A-Za-z0-9._-]{1,80}$"}, "minItems": 2, "maxItems": 4}}, "required": ["names"], "additionalProperties": False}},
 {"name": "convert_units", "description": "Convert a quantity between units of data size (B, KB, MB, GB, TB) or time (ms, s, min, h, day).",
  "parameters": {"type": "object", "properties": {"value": {"type": "number"}, "from_unit": {"type": "string"}, "to_unit": {"type": "string"}}, "required": ["value", "from_unit", "to_unit"], "additionalProperties": False}}]
SCHEMA = {s["name"]: s["parameters"] for s in SPECS}
def _pypi(name):
    r = requests.get(f"https://pypi.org/pypi/{name}/json", headers=UA, timeout=10)
    if r.status_code == 404: return {"error": f"no package called {name!r} on PyPI"}
    d = r.json(); i = d["info"]; rel = d["releases"].get(i["version"]) or [{}]
    return dict(name=i["name"], version=i["version"], released=(rel[0].get("upload_time") or "")[:10], summary=i["summary"], licence=i.get("license_expression") or (i.get("license") or "")[:30], releases=len(d["releases"]), url=f"https://pypi.org/project/{i['name']}/")
def get_package_info(name): return _pypi(name)
def search_github(query, language=None, sort="stars", limit=5):
    q = query + (f" language:{language}" if language else ""); r = requests.get("https://api.github.com/search/repositories", params={"q": q, "sort": sort, "per_page": limit}, headers=UA, timeout=10).json()
    return [dict(repo=x["full_name"], stars=x["stargazers_count"], updated=x["pushed_at"][:10], description=(x.get("description") or "")[:100], url=x["html_url"]) for x in r.get("items", [])]
def compare_packages(names): return [_pypi(n) for n in names]
UNITS = {"b": ("data", 1), "kb": ("data", 1024), "mb": ("data", 1024 ** 2), "gb": ("data", 1024 ** 3), "tb": ("data", 1024 ** 4),
         "ms": ("time", .001), "s": ("time", 1), "min": ("time", 60), "h": ("time", 3600), "day": ("time", 86400)}
def convert_units(value, from_unit, to_unit):
    a, b = UNITS.get(from_unit.lower().rstrip("s") if from_unit.lower() not in UNITS else from_unit.lower()), UNITS.get(to_unit.lower() if to_unit.lower() in UNITS else to_unit.lower().rstrip("s"))
    if not a or not b or a[0] != b[0]: return {"error": f"can't convert {from_unit} to {to_unit}"}
    return dict(value=value, from_unit=from_unit, to_unit=to_unit, result=round(value * a[1] / b[1], 6))
IMPL = dict(get_package_info=get_package_info, search_github=search_github, compare_packages=compare_packages, convert_units=convert_units)
def execute(call):
    """Validate a {name, arguments} call against its schema, then run it. Errors are returned (not raised) so the model can fix its call."""
    name, args = call.get("name"), call.get("arguments", {})
    if isinstance(args, str):
        try: args = json.loads(args)
        except json.JSONDecodeError as e: return dict(ok=False, error=f"arguments are not valid JSON: {e}")
    if name not in IMPL: return dict(ok=False, error=f"unknown function {name!r}; available: {list(IMPL)}")
    try: jsonschema.validate(args, SCHEMA[name])
    except jsonschema.ValidationError as e: return dict(ok=False, error=f"invalid arguments for {name}: {e.message}")
    try: return dict(ok=True, result=IMPL[name](**args))
    except requests.RequestException as e: return dict(ok=False, error=f"API error: {type(e).__name__}")
