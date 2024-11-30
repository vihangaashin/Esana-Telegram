# Use the official Python image as the base
FROM python:3.9.18

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of your application code
COPY . /app/

# Set the environment variable for the app
ENV PYTHONUNBUFFERED 1

# Run the application
CMD ["python", "main.py"]
