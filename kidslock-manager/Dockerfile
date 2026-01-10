FROM python:3.11-alpine

# Installeer systeem tools (ping en sqlite)
RUN apk add --no-cache iputils sqlite bash

WORKDIR /app

# Kopieer en installeer eisen
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest
COPY . .

# Maak run.sh uitvoerbaar
RUN chmod a+x run.sh

# In een standaard Alpine image MOETEN we wel CMD gebruiken
# omdat we de s6-overlay niet gebruiken.
CMD ["python", "main.py"]