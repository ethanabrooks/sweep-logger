# inspired by https://sourcery.ai/blog/python-docker/ 
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
ENV VIRTUAL_ENV=/project/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# common dependencies
RUN apt-get update -q \
 && DEBIAN_FRONTEND="noninteractive" \
    apt-get install -yq \
      # primary interpreter
      python3.8 \

      # redis-python
      redis \

 && apt-get clean

FROM base AS python-deps

# build dependencies
RUN apt-get update -q \
 && DEBIAN_FRONTEND="noninteractive" \
    apt-get install -yq \

      # required by poetry
      python \  
      python3-pip \ 

      # required for redis
      gcc \

 && apt-get clean

WORKDIR "/deps"

COPY pyproject.toml poetry.lock /deps/
RUN python3.8 -m pip install poetry && poetry install

FROM base AS runtime

WORKDIR "/project"
COPY --from=python-deps /root/.cache/pypoetry/virtualenvs/ppo-K3BlsyQa-py3.8 /project/venv
COPY . .

ENTRYPOINT ["python", "sweep_logger/main.py"]
