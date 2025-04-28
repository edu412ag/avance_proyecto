FROM python:3.9-slim

WORKDIR /web

COPY . /web/


RUN pip install --no-cache-dir -r web/requirements.txt


EXPOSE 5001




CMD ["flask", "run"]