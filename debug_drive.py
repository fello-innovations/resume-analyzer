"""Debug script to inspect what the Drive API actually returns."""
import sys
sys.path.insert(0, ".")
from gdrive.auth import get_drive_service

folder_id = "1TXQSGyUFcK8xpU_7lPkG8qXlvIMHp_bl"
service = get_drive_service()

# Try with supportsAllDrives to handle shared drives
response = service.files().list(
    q=f"'{folder_id}' in parents and trashed=false",
    fields="nextPageToken, files(id, name, mimeType, webViewLink)",
    pageSize=10,
    supportsAllDrives=True,
    includeItemsFromAllDrives=True,
).execute()

files = response.get("files", [])
print(f"Found {len(files)} files")
for f in files[:10]:
    print(f"  {f['name']} — {f['mimeType']}")

if not files:
    # Try listing without parent filter to check access
    print("\nChecking folder metadata...")
    try:
        folder = service.files().get(
            fileId=folder_id,
            fields="id, name, mimeType",
            supportsAllDrives=True,
        ).execute()
        print(f"Folder accessible: {folder}")
    except Exception as e:
        print(f"Cannot access folder: {e}")
