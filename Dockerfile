FROM nikolaik/python-nodejs:python3.9-nodejs16

RUN apt update && apt upgrade -y
RUN apt install ffmpeg -y

COPY requirements.txt /requirements.txt
RUN cd /
RUN pip3 install -U pip && pip3 install -U -r requirements.txt
RUN mkdir /VCPlayerBot
WORKDIR /VCPlayerBot
COPY start.sh /start.sh
CMD ["/bin/bash", "/start.sh"]
