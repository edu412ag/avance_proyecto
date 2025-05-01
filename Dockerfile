FROM python:3.9-slim

WORKDIR /web

COPY . .

RUN pip install --no-cache-dir -r web/requirements.txt

ENV FLASK_APP=web/aparte.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5002

EXPOSE 5002

CMD ["flask", "run"]