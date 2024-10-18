FROM alpine:3.19

RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN apk add --no-cache chromium chromium-chromedriver unzip
RUN apk add --update --no-cache py3-pip

ENV BOT_TOKEN=7776316269:AAES2yNl__LEAsFJDIlxcK0ZytLwX-oO5Co`
ENV BOT_GroupID=-4026028372

WORKDIR /usr/src/app
COPY src .
COPY .env .
RUN pip install --no-cache-dir -r ./requirements.txt --break-system-packages

CMD [ "python", "./main.py" ]
EXPOSE 80