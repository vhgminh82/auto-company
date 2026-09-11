FROM mcr.microsoft.com/playwright/python:v1.55.0-noble

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY craw_country ./craw_country
COPY craw_data ./craw_data
COPY README.md ./README.md

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 9997

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9997"]
