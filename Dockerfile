# syntax=docker/dockerfile:1.4
FROM python:3.11.9-slim-bullseye

WORKDIR /var/www/server
COPY . .
RUN pip3 install -r requirements.txt

EXPOSE 5001

CMD ["python3", "app.py"]