import requests
import config

def upload_to_gofile(filepath):
    # ✅ यहाँ अपनी GoFile.io की Personal API Token डालें
    GOFILE_API_TOKEN = "YOUR_REAL_API_TOKEN"

    with open(filepath, 'rb') as f:
        response = requests.post(
            "https://api.gofile.io/uploadFile",
            files={"file": f},
            data={"token": GOFILE_API_TOKEN}
        )

    try:
        data = response.json()
        if data.get("status") == "ok":
            return data["data"]["downloadPage"]
        else:
            print("Upload failed:", data)
            return None
    except Exception as e:
        print("GoFile response (not json):", response.text)
        return None
