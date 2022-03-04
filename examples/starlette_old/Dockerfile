FROM python:3.7.4

ENV LC_ALL C.UTF-8
ENV LANG=C.UTF-8

WORKDIR /project

COPY Pipfile .
COPY whl whl

RUN pip install pipenv
RUN pipenv install --skip-lock --system
 

COPY . .

CMD gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --log-level info
