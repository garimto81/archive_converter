"""Upload WSOP data to Google Sheets"""

import json
import re
from pathlib import Path

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.run(["pip", "install", "gspread", "google-auth"], check=True)
    import gspread
    from google.oauth2.service_account import Credentials


def parse_wsop_data(json_path: Path) -> list:
    """Parse WSOP JSON data"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    videos = data.get('videos', [])
    parsed = []

    for v in videos:
        title = v.get('title', '')
        url = v.get('url', '')

        # Extract year
        year = None
        for y in range(2011, 2026):
            if str(y) in title:
                year = y
                break

        # Extract category
        if 'Main Event' in title:
            category = 'Main Event'
        elif 'Bracelet' in title:
            category = 'Bracelet Events'
        else:
            category = 'Other'

        # Extract event number
        event_match = re.search(r'Event #?(\d+)', title)
        event_num = int(event_match.group(1)) if event_match else None

        # Extract episode/day
        episode_match = re.search(r'Episode (\d+)', title)
        day_match = re.search(r'Day (\d+[A-D]?)', title)
        episode = episode_match.group(1) if episode_match else (day_match.group(1) if day_match else None)

        # Check HLS
        has_hls = 'O' if v.get('manifest_url') else 'X'

        parsed.append({
            'year': year,
            'category': category,
            'event_num': event_num,
            'episode': episode,
            'title': title,
            'url': url,
            'hls_url': v.get('manifest_url', ''),
            'has_hls': has_hls,
            'thumbnail': v.get('thumbnail', ''),
        })

    # Sort by year desc, category, event_num, episode
    parsed.sort(key=lambda x: (
        -(x['year'] or 0),
        x['category'],
        x['event_num'] or 999,
        x['episode'] or ''
    ))

    return parsed


def upload_to_sheets(data: list, sheet_id: str):
    """Upload data to Google Sheets"""
    # Credentials
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    # Try to find credentials file
    creds_paths = [
        Path(r'd:\AI\claude01\json\service_account_key.json'),
        Path('credentials.json'),
        Path('service_account.json'),
        Path.home() / '.config' / 'gcloud' / 'application_default_credentials.json',
        Path(__file__).parent.parent / 'credentials.json',
    ]

    creds_file = None
    for p in creds_paths:
        if p.exists():
            creds_file = p
            break

    if not creds_file:
        print("Error: No credentials file found.")
        print("Please place 'credentials.json' or 'service_account.json' in the project root.")
        print("\nAlternatively, exporting to CSV...")
        return export_to_csv(data)

    # Authenticate
    creds = Credentials.from_service_account_file(str(creds_file), scopes=scopes)
    client = gspread.authorize(creds)

    # Open sheet
    try:
        sheet = client.open_by_key(sheet_id)
    except gspread.SpreadsheetNotFound:
        print(f"Error: Sheet not found: {sheet_id}")
        return export_to_csv(data)

    # Get or create worksheet
    try:
        worksheet = sheet.worksheet('WSOP Videos')
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet('WSOP Videos', rows=len(data) + 1, cols=10)

    # Headers
    headers = ['Year', 'Category', 'Event #', 'Episode', 'Title', 'URL', 'HLS URL', 'Has HLS', 'Thumbnail']

    # Prepare data
    rows = [headers]
    for item in data:
        rows.append([
            item['year'] or '',
            item['category'],
            item['event_num'] or '',
            item['episode'] or '',
            item['title'],
            item['url'],
            item['hls_url'],
            item['has_hls'],
            item['thumbnail'],
        ])

    # Clear and update
    worksheet.clear()
    worksheet.update(rows, value_input_option='USER_ENTERED')

    print(f"Uploaded {len(data)} rows to Google Sheets")
    print(f"Sheet URL: https://docs.google.com/spreadsheets/d/{sheet_id}")

    return True


def export_to_csv(data: list) -> Path:
    """Export data to CSV as fallback"""
    import csv

    output_path = Path(__file__).parent.parent / 'data' / 'pokergo' / 'wsop_list.csv'

    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)

        # Headers
        writer.writerow(['Year', 'Category', 'Event #', 'Episode', 'Title', 'URL', 'HLS URL', 'Has HLS', 'Thumbnail'])

        for item in data:
            writer.writerow([
                item['year'] or '',
                item['category'],
                item['event_num'] or '',
                item['episode'] or '',
                item['title'],
                item['url'],
                item['hls_url'],
                item['has_hls'],
                item['thumbnail'],
            ])

    print(f"Exported {len(data)} rows to CSV: {output_path}")
    return output_path


def main():
    # Config - use merged data
    json_path = Path(__file__).parent.parent / 'data' / 'pokergo' / 'wsop_merged_20251216_133457.json'
    sheet_id = '1h27Ha7pR-iYK_Gik8F4FfSvsk4s89sxk49CsU3XP_m4'

    print("Parsing WSOP data...")
    data = parse_wsop_data(json_path)
    print(f"Found {len(data)} videos")

    # Year summary
    years = {}
    for item in data:
        y = item['year']
        years[y] = years.get(y, 0) + 1

    print("\nBy Year:")
    for y in sorted([k for k in years.keys() if k is not None], reverse=True):
        print(f"  {y}: {years[y]}")
    if None in years:
        print(f"  Unknown: {years[None]}")

    print("\nUploading to Google Sheets...")
    upload_to_sheets(data, sheet_id)


if __name__ == '__main__':
    main()
