FROM python:bullseye

RUN pip install poetry
WORKDIR /code
COPY . /code
RUN poetry install
CMD poetry run start