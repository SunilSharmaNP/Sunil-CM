import os
from aiofiles.os import path as aiopath
from aiohttp import ClientSession, FormData
from random import choice

class GofileUploader:
    def __init__(self, token=None):
        """
        Initialize GoFile uploader.

        Args:
            token (str): GoFile API token.
        """
        self.api_url = "https://api.gofile.io/"
        self.token = token

    async def __get_server(self):
        """
        Get a random GoFile upload server from the API.

        Returns:
            str: Server name.
        """
        async with ClientSession() as session:
            async with session.get(f"{self.api_url}servers") as resp:
                result = await resp.json()
                if result.get("status") == "ok":
                    servers = result["data"]["servers"]
                    return choice(servers)["name"]
                raise Exception("Failed to fetch GoFile upload server.")

    async def upload_file(self, file_path: str):
        """
        Upload a file to GoFile.io asynchronously.

        Args:
            file_path (str): Path to the file to be uploaded.

        Returns:
            str: URL of the uploaded file's download page.

        Raises:
            ValueError: If GoFile token is missing.
            FileNotFoundError: If file does not exist.
            Exception: For any upload failure or unexpected API response.
        """
        if not self.token:
            raise ValueError("❌ GoFile API token is missing. Please check config or environment variable.")

        if not await aiopath.isfile(file_path):
            raise FileNotFoundError(f"❌ File not found: {file_path}")

        server = await self.__get_server()
        upload_url = f"https://{server}.gofile.io/uploadFile"

        data = FormData()
        data.add_field("token", self.token)

        try:
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
        except Exception as e:
            # Re-raise exception for the caller to handle
            raise e
