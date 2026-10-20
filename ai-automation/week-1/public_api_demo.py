"""Read a public JSON endpoint; no key or account is needed for this demo."""
import json, urllib.request
URLS = [
    "https://api.github.com/repos/python/cpython",
    "https://api.github.com/repos/nodejs/node",
    "https://api.github.com/repos/microsoft/vscode",
]
for url in URLS:
    request = urllib.request.Request(url, headers={"User-Agent":"skillnexis-week1-demo"})
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status != 200: raise RuntimeError(f"{url}: HTTP {response.status}")
        data = json.load(response)
    print(data.get("full_name"), "stars:", data.get("stargazers_count"), "description:", data.get("description"))
