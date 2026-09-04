FROM python:3.12-slim

WORKDIR /app

# Τα requirements αντιγράφονται πρώτα και μόνα τους: όσο δεν αλλάζουν, το
# Docker επαναχρησιμοποιεί το cached layer του pip install σε κάθε rebuild.
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 120 --retries 10 -r requirements.txt

COPY . .

EXPOSE 8000

# 0.0.0.0 και όχι 127.0.0.1: μέσα σε container το loopback interface δεν
# είναι προσβάσιμο απ' έξω, οπότε το port mapping δεν θα έφτανε στον server.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
