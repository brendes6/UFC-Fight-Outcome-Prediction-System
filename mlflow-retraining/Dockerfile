FROM python:3.9-slim
WORKDIR /app

RUN pip install --no-cache-dir \
    pandas numpy scikit-learn mlflow \
    google-cloud-firestore google-cloud-storage && \
    pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu

COPY . .

CMD ["python", "main.py"]