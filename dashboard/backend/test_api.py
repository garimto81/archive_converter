"""
Simple API test script for development.
Run this after starting the server to verify all endpoints.
"""
import httpx
import asyncio


async def test_api():
    """Test all API endpoints"""
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        print("Testing Archive Dashboard Backend API")
        print("=" * 60)

        # Test health
        print("\n1. Health Check:")
        response = await client.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        # Test matching matrix
        print("\n2. Matching Matrix:")
        response = await client.get(f"{base_url}/api/matching/matrix")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Total Files: {data['total_files']}")
        print(f"   Total Segments: {data['total_segments']}")
        print(f"   Matched Files: {data['matched_files']}")
        print(f"   Items: {len(data['items'])}")

        # Test status filter
        print("\n3. Matching Matrix (partial only):")
        response = await client.get(f"{base_url}/api/matching/matrix?status=partial")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Filtered Items: {len(data['items'])}")
        if data['items']:
            print(f"   First Item: {data['items'][0]['file_name']} ({data['items'][0]['status_detail']})")

        # Test search
        print("\n4. Matching Matrix (search 'STREAM'):")
        response = await client.get(f"{base_url}/api/matching/matrix?search=STREAM")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Search Results: {len(data['items'])}")
        for item in data['items'][:3]:
            print(f"   - {item['file_name']}: {item['segment_count']} segments")

        # Test stats
        print("\n5. Matching Stats:")
        response = await client.get(f"{base_url}/api/matching/stats")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   NAS Files: {data['sources']['nas']['total_files']}")
        print(f"   Archive Records: {data['sources']['archive_metadata']['total_records']}")
        print(f"   Iconik Records: {data['sources']['iconik_metadata']['total_records']}")
        print(f"   Complete Files: {data['matching']['files']['complete']}")
        print(f"   Partial Files: {data['matching']['files']['partial']}")
        print(f"   Segment Conversion Rate: {data['coverage']['segment_conversion_rate']:.2%}")

        # Test file segments
        print("\n6. File Segments (STREAM_01.mp4):")
        response = await client.get(f"{base_url}/api/matching/file/STREAM_01.mp4/segments")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   File: {data['file_name']}")
        print(f"   Total Segments: {data['total_segments']}")
        print(f"   Converted Segments: {data['converted_segments']}")
        if data['segments']:
            seg = data['segments'][0]
            print(f"   First Segment:")
            print(f"   - Time: {seg['time_range']['in_tc']} → {seg['time_range']['out_tc']}")
            print(f"   - Rating: {seg['metadata']['rating']} stars")
            print(f"   - Winner: {seg['metadata']['winner']}")
            print(f"   - UDM Status: {seg['udm']['status']}")

        # Test NAS folders
        print("\n7. NAS Folders:")
        response = await client.get(f"{base_url}/api/nas/folders")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Root: {data['root']['name']}")
        print(f"   Children: {len(data['root']['children'])}")
        for folder in data['root']['children']:
            print(f"   - {folder['name']}: {folder['file_count']} files, {folder['folder_count']} folders")

        # Test NAS files
        print("\n8. NAS Files (/ARCHIVE/WSOP/STREAM):")
        response = await client.get(f"{base_url}/api/nas/files?path=/ARCHIVE/WSOP/STREAM")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Path: {data['path']}")
        print(f"   Total Files: {data['total']}")
        for file in data['files'][:3]:
            print(f"   - {file['name']}: {file['size_mb']:.1f} MB, Has Metadata: {file['has_metadata']}")

        print("\n" + "=" * 60)
        print("All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_api())
