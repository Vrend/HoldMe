FROM redis
LABEL maintainer="Vrend"
RUN apt-get update -y
RUN apt-get install -y python3 python3-dev python3-pip

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY . /app

EXPOSE 5000
ENTRYPOINT ["sh", "run.sh"]
