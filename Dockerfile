FROM python:3.10.7

WORKDIR /app

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Install supervisord
RUN apt-get update && apt-get install -y supervisor

# Copy the rest of the application
COPY . .

# Copy supervisord configuration file

# Expose necessary ports
EXPOSE 8018 8055

# Start supervisord to manage the processes
# CMD ["supervisord", "-c", "supervisord.conf"]

# Run all processes in the foreground
# CMD bash -c "uvicorn talent_bridged.asgi:application --host 0.0.0.0 --port 8018 & \
#               celery -A talent_bridged.celery worker -l info -n talent_bridged_worker & \
#               celery -A talent_bridged beat -l info & \
#               celery -A talent_bridged flower --port=8055"

CMD bash -c "uvicorn talent_bridged.asgi:application --host 0.0.0.0 --port 8018 & \
              celery -A talent_bridged.celery worker -l info -n talent_bridged_worker & \
              celery -A talent_bridged beat -l info & \
              celery -A talent_bridged flower --port=8055"