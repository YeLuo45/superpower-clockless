#!/usr/bin/env python3
"""
Backup proposals data from ai-superpower API.
Usage: backup_api.py <backup_dir> <api_key> <api_base>
"""

import os, sys, subprocess, json, csv

def curl_get(api_key, base, path):
    r = subprocess.run(
        ["curl", "-s", f"{base}{path}",
         "-H", f"X-API-Key: {api_key}"],
        capture_output=True, text=True, timeout=15
    )
    return json.loads(r.stdout)

def fetch_all(api_key, base, endpoint, page_size=200):
    items = []
    page = 1
    while True:
        try:
            data = curl_get(api_key, base, f"/api/{endpoint}?page={page}&page_size={page_size}")
            page_items = data.get("items", [])
            if not page_items:
                break
            items.extend(page_items)
            total = data.get("total", 0)
            if len(items) >= total:
                break
            page += 1
            if page > 100:
                break
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break
    return items

def main():
    backup_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp"
    api_key = os.environ.get("SUPERPOWER_API_KEY", sys.argv[2] if len(sys.argv) > 2 else "")
    api_base = os.environ.get("AI_SUPERPOWER_BASE", sys.argv[3] if len(sys.argv) > 3 else "http://0.0.0.0:8000")

    # Fetch and save projects
    print("  获取 projects... ", end="", flush=True)
    projects = fetch_all(api_key, api_base, "projects")
    if projects:
        keys = list(projects[0].keys())
        with open(f"{backup_dir}/projects.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(projects)
        print(f"✅ {len(projects)} projects")
    else:
        print("⚠️  无数据")

    # Fetch and save proposals
    print("  获取 proposals... ", end="", flush=True)
    proposals = fetch_all(api_key, api_base, "proposals")
    if proposals:
        keys = list(proposals[0].keys())
        with open(f"{backup_dir}/proposals.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(proposals)
        print(f"✅ {len(proposals)} proposals")
    else:
        print("⚠️  无数据")

if __name__ == "__main__":
    main()