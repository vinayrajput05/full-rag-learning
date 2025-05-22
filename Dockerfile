FROM python:latest

RUN apt-get update
RUN apt-get install -y poppler-utils

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY app/ /app/app/

CMD [ "/bin/sh", "-c", "python -m app.main"]