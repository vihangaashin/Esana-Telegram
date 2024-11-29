# Use the official Python image as the base
FROM python:3.9.18

# Set the working directory
WORKDIR /app

# Copy the Pipfile and Pipfile.lock to the container
COPY Pipfile Pipfile.lock /app/

# Install pipenv and dependencies
RUN pip install --upgrade pip && \
    pip install pipenv && \
    pipenv install --deploy --ignore-pipfile

# Copy the rest of your application code
COPY . /app/

# Set the environment variable for the app
ENV PYTHONUNBUFFERED 1

# Run the application
CMD ["pipenv", "run", "python", "main.py"]
