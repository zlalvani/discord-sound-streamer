FROM python:3.10-bullseye

RUN pip install poetry
WORKDIR /code
COPY . /code
RUN poetry install
CMD poetry run start
