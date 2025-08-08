import os
from aiofiles.os import path as aiopath
from aiohttp import ClientSession
from random import choice
import config

class GofileUploader:
    def __init__(self, token=None):
        self.api_url = "https://api.gofile.io/"
        self.token = token

    async def __get_server(self):
        async with ClientSession() as session:
            async with session.get(f"{self.api_url}servers") as resp:
                result = await resp.json()
                if result.get("status") == "ok":
                    return choice(result["data"]["servers"])["name"]
                raise Exception("Failed to fetch GoFile upload server")

    async def upload_file(self, file_path: str):
        if not await aiopath.isfile(file_path):
            raise FileNotFoundError("File not found.")

        server = await self.__get_server()
        upload_url = f"https://{server}.gofile.io/uploadFile"

        data = {
            "token": self.token
        }

        async with ClientSession() as session:
            with open(file_path, "rb") as f:
                form_data = {
                    "file": f
                }
                async with session.post(upload_url, data=data, files=form_data) as resp:
                    try:
                        out = await resp.json()
                        if out.get("status") == "ok":
                            return out["data"]["downloadPage"]
                        else:
                            raise Exception(f"Upload failed: {out}")
                    except Exception:
                        text = await resp.text()
                        raise Exception(f"Unexpected GoFile response: {text}")
                        
