FROM python:3.12-slim

WORKDIR /app

RUN pip install fastapi uvicorn python-dotenv sharkiq

COPY main.py ./

EXPOSE 8001

CMD ["python", "main.py"]
