FROM python:3.12-alpine3.18
LABEL maintainer="oleksandrturulko@gmail.com"

ENV PYTHONUNBUFFERED 1

WORKDIR /app/

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

# Create needed dirs
RUN mkdir -p /files/media /app/static /app/media

# Add system user
RUN adduser \
    --disabled-password \
    --no-create-home \
    app_user

# Fix permissions
RUN chown -R app_user:app_user /files/media /app/static /app/media
RUN chmod -R 755 /files/media /app/static /app/media

USER app_user

CMD ["sh", "-c", "python manage.py wait_for_db && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
