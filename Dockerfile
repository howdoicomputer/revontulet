FROM python:3.13-slim
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt
COPY . /code/revontulet
EXPOSE 8000
CMD ["fastapi", "run", "revontulet/main.py", "--port", "8000"]
