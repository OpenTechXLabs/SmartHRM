# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and environment variable file
COPY requirements.txt ./
COPY .env ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port that the app runs on
EXPOSE 8008

# Run the FastAPI app using Uvicorn with auto-reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8008", "--reload"] 
