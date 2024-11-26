# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set environment variables

# Set the working directory
WORKDIR /app

# Copy the requirements file and .env into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI application code into the container
COPY . .

# Expose the port that the FastAPI app runs on
EXPOSE 8004

# Command to run the application using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
