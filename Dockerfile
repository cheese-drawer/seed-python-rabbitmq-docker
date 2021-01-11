FROM python:alpine

WORKDIR /opt/app
ADD app .
# ENTRYPOINT ["/bin/sh"]

RUN pip3 install -r requirements.txt

ENV FLASK_APP=/opt/app/src/server.py
ENV FLASK_ENV=production
ENTRYPOINT ["python"]
# specifying host as 0.0.0.0 allows access from outside container
# port isn't specified to allow server.py to get it from runtime
# via -e FLASK_RUN_PORT={port number} or via docker-compose.yml's
# `environment` key for this image, like so:
# ```
# image:
#   environment:
#     - FLASK_RUN_PORT: {some port number}
# ```
# unlike the DEV image, this image requires the SERVER_PORT to be
# manually set in the environment; the server will error out
# without it
CMD ["-m", "flask", "run", "--host=0.0.0.0"]
