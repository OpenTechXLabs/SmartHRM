# Use the official Python image as a base
FROM python:3.10-alpine3.20

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy requirements.txt to the working directory
COPY requirements.txt .

# Install the necessary packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files to the container
COPY . .

EXPOSE 8002

# Command to run your application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]
