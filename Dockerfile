FROM python:3-slim-buster

RUN apt-get update -y
RUN apt-get install -y build-essential

WORKDIR /

COPY ./requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . /

ENTRYPOINT [ "python" ]

CMD [ "metal_ra.py" ]
