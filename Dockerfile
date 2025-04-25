FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    openjdk-17-jdk \
    python3 \
    python3-pip \
    curl \
    unzip \
    git

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

WORKDIR /app

COPY . /app

RUN pip3 install -r requirements.txt

CMD ["python3", "bot.py"]
