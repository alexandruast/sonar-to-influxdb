FROM python:3.6-alpine as BUILDER
MAINTAINER Alexandru Ast <alexandru.ast@gmail.com>

ENV APP_HOME=/build
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

COPY . .

RUN pip install -r requirements.txt \
&& python sonar-to-influxdb.py

FROM python:3.6-alpine

COPY [ \
  "requirements.txt", \
  "sonar-to-influxdb.py -h", \
   "/" \
]

RUN pip install -r requirements.txt

CMD ["python", "sonar-to-influxdb.py"]