FROM python:3

WORKDIR /usr/src/app

COPY ./Pipfile ./
RUN pip install --no-cache-dir pipenv
RUN pipenv install --system --skip-lock

COPY . .

RUN pip install -e .
