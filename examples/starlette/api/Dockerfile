FROM python:3-slim

WORKDIR /srv/user
EXPOSE 8000

RUN useradd user --home /home/user && \
    mkdir -p /home/user && \
    chown -R user:user /home/user && \
    chown -R user:user /srv/user
USER user

RUN pip install starlette starlette-zipkin uvicorn

COPY ./app.py /srv/user/
CMD ["python", "app.py"]
