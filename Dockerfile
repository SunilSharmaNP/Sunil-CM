# --- Dockerfile ---

# 1. Python base image
FROM python:3.10-slim

# 2. System dependencies (ffmpeg आदि)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# 3. Workdir सेट करें
WORKDIR /app

# 4. Source code कॉपी करें
COPY . /app

# 5. Python dependencies इंस्टॉल करें
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 6. कमांड (Bot स्टार्ट)
CMD ["python", "bot.py"]
