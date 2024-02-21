FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Labels
MAINTAINER Adams Pierre David <adamspd.developer@gmail.com>
LABEL version="1.0"
LABEL description="Docker Image to test django-appointment package in a container."

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV NAME World

# Run migrations and collect static files
RUN python manage.py makemigrations
RUN python manage.py migrate

# Run the command to start uWSGI
CMD ["uwsgi", "--http", ":8000", "--module", "django_appointment.wsgi"]
