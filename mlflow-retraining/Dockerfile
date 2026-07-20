FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir \
    torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu

COPY . .

CMD ["python", "main.py"]