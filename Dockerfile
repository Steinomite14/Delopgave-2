
# Brug Python 3.12 som grundlag
FROM python:3.12-slim

# Opret projektmappen inde i containeren
WORKDIR /app

# Kopier listen over Python-biblioteker
COPY requirements.txt .

# Installer de nødvendige biblioteker
RUN pip install --no-cache-dir -r requirements.txt

# Kopier projektets kode ind i containeren
COPY . .

# Flask API'et kører på port 5000 i containeren
EXPOSE 5000

# Start Flask API'et med Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
