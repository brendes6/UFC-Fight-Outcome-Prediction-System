FROM python:3.9-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu

COPY . .

CMD ["python", "main.py"]