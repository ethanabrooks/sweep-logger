FROM python:3.8-slim as base

# Setup locale
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# no .pyc files
ENV PYTHONDONTWRITEBYTECODE 1

# traceback on segfau8t
ENV PYTHONFAULTHANDLER 1

# use ipdb for breakpoints
ENV PYTHONBREAKPOINT=ipdb.set_trace

# source virtualenv
#ENV VIRTUAL_ENV=/home/.venv
#ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# common dependencies
RUN apt-get update -q \
 && DEBIAN_FRONTEND="noninteractive" \
    apt-get install -yq \

      # required for redis
      gcc \
      redis \

      # required for run_logger
      git \
 && apt-get clean


WORKDIR /home
COPY pyproject.toml poetry.lock /home/

RUN pip install poetry\
 && poetry install

COPY . .

VOLUME /config
ENTRYPOINT ["poetry", "run", "python", "create_sweep.py"]
