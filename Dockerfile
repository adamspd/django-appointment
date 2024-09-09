FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Conditionally install django-q2
ARG USE_DJANGO_Q=False
RUN if [ "$USE_DJANGO_Q" = True ] ; then pip install django-q2 ; fi

# Labels
MAINTAINER Adams Pierre David <adamspd.developer@gmail.com>
LABEL version="1.0"
LABEL description="Docker Image to test django-appointment package in a container."

# Define environment variable
ENV NAME World

