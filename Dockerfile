FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY teams.py /app/teams.py
COPY teams.db /app/teams.db

EXPOSE 5000

CMD ["flask", "--app", "teams:app", "run", "--host=0.0.0.0", "--port=5000"]
