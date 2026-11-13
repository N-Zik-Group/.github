import json
import os
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

org = "N-Zik-Group"
headers = {"Accept": "application/vnd.github+json", "User-Agent": "nzik-profile-contributors"}
if token := os.environ.get("GH_TOKEN"):
    headers["Authorization"] = f"Bearer {token}"

def pages(endpoint):
    url = f"https://api.github.com/{endpoint}?per_page=100"
    while url:
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            yield from json.load(response)
            links = response.headers.get("Link", "").split(",")
            url = next((part.split(">", 1)[0].strip()[1:] for part in links if 'rel="next"' in part), None)

contributors = {}
for repo in pages(f"orgs/{org}/repos"):
    if repo["private"] or repo["name"].startswith("."):
        continue
    for user in pages(f"repos/{repo['full_name']}/contributors"):
        if user["type"] == "User":
            contributors[user["id"]] = user

if not contributors:
    raise SystemExit("GitHub returned no contributors")
rows = []
for user in sorted(contributors.values(), key=lambda user: user["login"].casefold()):
    profile = escape(user["html_url"], quote=True)
    avatar = escape(user["avatar_url"], quote=True)
    login = escape(user["login"], quote=True)
    rows.append(f'<a href="{profile}"><img src="{avatar}" width="54" height="54" alt="{login}" title="{login}" /></a>')
path = Path("profile/README.md")
before, rest = path.read_text(encoding="utf-8").split("<!-- ecosystem-contributors:start -->", 1)
_, after = rest.split("<!-- ecosystem-contributors:end -->", 1)
grid = '<p align="center">\n' + "\n".join(rows) + "\n</p>"
path.write_text(before + "<!-- ecosystem-contributors:start -->\n" + grid + "\n<!-- ecosystem-contributors:end -->" + after, encoding="utf-8", newline="\n")
print(f"{len(rows)} contributors")
