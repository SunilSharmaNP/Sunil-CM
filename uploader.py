import os
from aiofiles.os import path as aiopath
from aiohttp import ClientSession, FormData
from random import choice

class GofileUploader:
    def __init__(self, token=None):
        self.api_url = "https://api.gofile.io/"
        self.token = token

    async def __get_server(self):
        async with ClientSession() as session:
            async with session.get(f"{self.api_url}servers") as resp:
                result = await resp.json()
                if result.get("status") == "ok":
                    servers = result["data"]["servers"]
                    return choice(servers)["name"]
                raise Exception("Failed to fetch GoFile upload server.")

    async def upload_file(self, file_path: str):
        if not self.token:
            raise ValueError("❌ GoFile API token is missing. Please check config or environment variable.")

        if not await aiopath.isfile(file_path):
            raise FileNotFoundError(f"❌ File not found: {file_path}")

        server = await self.__get_server()
        upload_url = f"https://{server}.gofile.io/uploadFile"

        data = FormData()
        data.add_field("token", self.token)

        with open(file_path, "rb") as f:
            data.add_field(
                "file",
                f,
                filename=os.path.basename(file_path),
                content_type="application/octet-stream"
            )

            async with ClientSession() as session:
                async with session.post(upload_url, data=data) as resp:
                    try:
                        resp_json = await resp.json()
                        if resp_json.get("status") == "ok":
                            return resp_json["data"]["downloadPage"]
                        else:
                            raise Exception(f"Upload failed: {resp_json}")
                    except Exception:
                        text = await resp.text()
                        raise Exception(f"Unexpected GoFile response: {text}")
                        
