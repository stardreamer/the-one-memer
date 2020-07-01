FROM python:3.8.0-slim
RUN apt-get update \
&& apt-get install gcc -y \
&& apt-get clean

WORKDIR /app
COPY . ./

RUN pip install poetry

RUN poetry install

CMD ["poetry", "run", "python", "./reddit_grabber/main.py" ]