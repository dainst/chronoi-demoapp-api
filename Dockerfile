
FROM python:3.8

# poetry is installed system-wide
RUN pip install poetry==1.0.5

# the rest of the script has an unprivileged user
RUN useradd -ms /bin/bash  demoapp
USER demoapp

# Copy only the dependency files first, to cache the installation
WORKDIR /app
COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false \
    && poetry install $(test "$FLASK_ENV" = "production" && echo "--no-dev") --no-interaction

# Copy the rest of the files
COPY . /app

ENTRYPOINT [ "/app/app.py" ]
