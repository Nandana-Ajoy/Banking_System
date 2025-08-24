FROM python:latest

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

#SAVE AND BUILD THE DOCKER IMAGE