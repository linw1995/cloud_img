FROM python:3

WORKDIR /usr/src/app

COPY . .

RUN pip install pipenv
RUN pipenv --three

RUN pipenv install --deploy -e .

RUN cp conf.docker-compose.yaml conf.yaml

ENTRYPOINT [ "pipenv", "run" ]
