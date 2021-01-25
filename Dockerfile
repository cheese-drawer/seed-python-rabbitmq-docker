FROM python:alpine

RUN mkdir /app
WORKDIR /app
COPY app /app

# Enable easy dev on active container by using a bind mount via -v
# to give the container access to the source code on your machine
# For example, assuming you have a project directory structure like this:
# .
# |_ Dockerfile
# |_ README
# |_ .gitignore
# |_ app/
#   |_ .env/ ... python environment, local only
#   |_ .python-version
#   |_ requirements.txt
#   |_ .pylintrc
#   |_ src/
#     |_ server.py
#     |_ some_other_file.py
#       ... more application files here
#
# and you wanted to be able to develop the application files while
# running a container for dev purposes, you would bind the ./app
# directory in your project directory to the container's /app
# directory using `docker run -v ./app:/app ...` from your project root
VOLUME /app

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python"]
CMD ["app/src/server.py"]
