FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/scraped_data /app/planilhas

EXPOSE 8080

CMD ["python", "src/main.py"]