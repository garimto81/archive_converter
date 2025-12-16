"""앱에 JSON 업로드"""

import requests
from pathlib import Path

API_URL = "http://127.0.0.1:8001/api/videos/import"
JSON_FILE = Path(__file__).parent.parent / "data" / "pokergo" / "wsop_for_app_20251216_155853.json"


def main():
    print(f"Uploading: {JSON_FILE}")

    with open(JSON_FILE, "rb") as f:
        files = {"file": (JSON_FILE.name, f, "application/json")}
        response = requests.post(API_URL, files=files)

    if response.status_code == 200:
        result = response.json()
        print(f"[OK] Imported: {result.get('imported', 0)} / {result.get('total', 0)}")
    else:
        print(f"[ERROR] {response.status_code}: {response.text}")


if __name__ == "__main__":
    main()
