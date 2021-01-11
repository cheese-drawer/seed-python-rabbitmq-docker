# Simple Flask server on Docker

The following seed project can be used to set up any Flask-based server to run in Docker. The project structure places the Docker & dev environment files at the root, with the python application inside `./app`:

```
.
|_ .envrc                 # automating python venv configuration via direnv
|_ .python-version        # specify python version here, used by .envrc/direnv
|_ Dockerfile
|_ app/
    |_ .secrets           # secret environment variables, not commited to get
    |_ requirements.txt   # recursively installs requirements/prod.txt
    |_ requirements
    |   |_ dev.txt        # development only pip packages, not installed on Docker
    |   |_ prod.txt       # production dependencies
    |_ src/               # application code
    |   |_ server.py
    |   |_ static/
    |   |_ templates/
    |_ tests/             # pytest tests
        |_ sever_spec.py  # structure should mirror that of ./app/src
```

To use this to seed a new project, just download a release, decompress it, and start modifying as needed. Alternatively, clone a branch to your local machine, then delete the `.git/` directory and init a new repo with `git init`.

To run run the service, first build your image using `docker build -t {YOUR_IMAGE_NAME_HERE} .`. When built, you can then start the service using the following `docker run` command:

```
docker run \
  -d \
  --env FLASK_ENV=development \
  --env FLASK_RUN_PORT=8000 \
  -p 8000:8000 \
  -v /home/andrew/dev/cheese-drawer/test-plaid/app:/opt/app \
  {YOUR_IMAGE_NAME_HERE}
```

This `run` command does the following:

1. Starts the container in detached mode, running it in the background
2. Tells Flask to run in development mode; can be changed to `--env FLASK_ENV=production` (or simply removed) if desired
3. Tells Flask to run the app on port 8000, this can be changed to any port you need, or eliminated to use Flask's default of 5000
4. Forwards the port to the host so it's available on localhost (and to other computers that can access the host), this should match the port specified at the previous line
5. Mounts the `./app` directory as a volume on the container, allowing you to make changes to the application without rebuilding the image
6. Runs the image you named in the previous `docker build ...` command
