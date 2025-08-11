FROM python:3.10

WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Install ffmpeg (Debian/Ubuntu base)
RUN apt-get update && apt-get install -y ffmpeg

CMD ["python3", "bot.py"]
