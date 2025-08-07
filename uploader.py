import requests

def upload_to_gofile(filepath):
    with open(filepath, 'rb') as f:
        response = requests.post(
            "https://api.gofile.io/uploadFile",
            files={"file": f}
        )
    data = response.json()
    if data.get("status") == "ok":
        return data["data"]["downloadPage"]
    else:
        return None
