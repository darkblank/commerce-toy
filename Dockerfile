FROM python:3.7

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y gdal-bin

COPY . /app
EXPOSE 8010
CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:8010"]