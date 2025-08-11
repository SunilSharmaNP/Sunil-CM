# ss-merger-bot

A Telegram bot to merge multiple videos (from direct links and Telegram uploads), with proper video+audio merging and GoFile.io upload.  
Now in English, user-friendly, and Heroku/Docker-ready.

## Features
- Merge videos from direct URLs or Telegram-uploaded files
- Proper FFmpeg handling (fallback to re-encoding if needed)
- English bot messages and instructions
- Upload merged file to GoFile.io for download
- Supports Heroku, Docker, Render, etc.

## Usage
1. Send `/start` or `/help` in the bot for instructions.
2. Send at least 2 video links:
    ```
    /merge link1 link2 link3
    ```
   Or upload at least 2 video files.
3. Bot downloads, merges, and uploads the result.
4. You receive a GoFile link 👍

## Deployment
- Set all environment variables: `API_ID`, `API_HASH`, `BOT_TOKEN`, `GOFILE_TOKEN`
- For Heroku: add `Procfile`, `runtime.txt`
- For Docker: use the provided `Dockerfile`

## Requirements
See `requirements.txt`

## License
MIT
