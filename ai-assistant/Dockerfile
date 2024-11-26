# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set environment variables

# Set the working directory
WORKDIR /app

# Copy the requirements file and .env into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install python-dotenv
RUN pip install mysql-connector-python==9.0.0
RUN pip install sqlglot==25.24.5

# Copy the FastAPI application code into the container
COPY . .

# Expose the port that the FastAPI app runs on
EXPOSE 8010

# Command to run the application using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]