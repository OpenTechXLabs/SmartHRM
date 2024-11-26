from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import requests
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file (optional)
load_dotenv()

# Initialize FastAPI app
app = FastAPI(root_path="/api/resume_upload")

# Add CORS middleware (for frontend testing, allows requests from any origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Local backend service URL for testing
# BACKEND_URL = "http://localhost:8000"  # Replace with your backend API URL if different
BACKEND_URL = "http://resume-s3:8000/api/resume_s3"
# Endpoint 1: Fetch all clients
@app.get("/clients")
def get_clients():
    try:
        clients_url = f"{BACKEND_URL}/clients"
        clients_response = requests.get(clients_url)
        clients_response.raise_for_status()  # Raise an exception for 4xx/5xx responses
        return clients_response.json()  # Return the list of clients
    except requests.RequestException as e:
        logger.error(f"Error fetching clients: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch clients.")

# Endpoint 2: Fetch job descriptions (positions) for a specific client
@app.get("/positions/{client_name}")
def get_positions(client_name: str):
    try:
        jd_url = f"{BACKEND_URL}/jd_filenames_by_name/{client_name}"
        jd_response = requests.get(jd_url)
        jd_response.raise_for_status()  # Raise an exception for 4xx/5xx responses
        return jd_response.json()  # Return job descriptions (positions)
    except requests.RequestException as e:
        logger.error(f"Error fetching job descriptions for client {client_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch job descriptions.")

# Endpoint 3: Upload resume for a specific client and job description
@app.post("/uploadResume")
async def upload_resume(
    file: UploadFile = File(...),
    client_name: str = Form(...),
    jd_filename: str = Form(...)
):
    # Step 1: Check if the client exists
    clients_url = f"{BACKEND_URL}/clients"
    try:
        clients_response = requests.get(clients_url)
        clients_response.raise_for_status()
        clients = clients_response.json()

        # Verify if the client exists in the list
        if not any(client['client_name'] == client_name for client in clients):
            raise HTTPException(status_code=404, detail="Client not found.")

    except requests.RequestException as e:
        logger.error(f"Error fetching clients: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch clients.")

    # Step 2: Check if the job description exists for the selected client
    jd_url = f"{BACKEND_URL}/jd_filenames_by_name/{client_name}"
    try:
        jd_response = requests.get(jd_url)
        jd_response.raise_for_status()
        job_descriptions = jd_response.json()

        # Verify if the JD filename exists in the fetched job descriptions
        if jd_filename not in job_descriptions['jd_filenames']:
            raise HTTPException(status_code=404, detail="Job description filename not found.")

    except requests.RequestException as e:
        logger.error(f"Error fetching job descriptions for client {client_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch job descriptions.")

    # Step 3: Upload the resume to the backend API
    upload_resume_url = f"{BACKEND_URL}/uploadResume"
    try:
        # Call the backend API to upload the resume
        resume_upload_response = requests.post(
            upload_resume_url,
            data={"client_name": client_name, "jd_filename": jd_filename},
            files={"file": (file.filename, file.file)}
        )
        resume_upload_response.raise_for_status()
        return resume_upload_response.json()  # Return the upload response
    except requests.RequestException as e:
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload resume.")

# Run locally with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
