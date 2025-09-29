FROM python:3.11-slim

WORKDIR /cli

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cli.py .

ENTRYPOINT ["python", "cli.py"]
