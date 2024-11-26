from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import requests
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(root_path="/api/jd_upload")

# Add CORS middleware
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




# Backend service URLs
#BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
BACKEND_URL = "http://jd-s3:8001/api/jd_s3"

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

# Endpoint 2: Post a new client (Using query parameters)
@app.post("/clients")
def post_client(client_name: str = Form(...)):
    try:
        create_client_url = f"{BACKEND_URL}/clients"
        logger.info(f"Creating client with name: {client_name}")
        
        # Send client_name as query parameter
        response = requests.post(create_client_url, params={"client_name": client_name})
        
        response.raise_for_status()  # Check for errors in the response
        logger.info(f"Client creation response: {response.json()}")  # Log the response
        return {"message": "Client created successfully!", "client": response.json()}
    except requests.HTTPError as e:
        logger.error(f"Error creating client {client_name}: {e}")
        logger.error(f"Response content: {response.content}")  # Log the response content for debugging
        raise HTTPException(status_code=500, detail="Failed to create client.")


# Endpoint 3: Upload a JD for a specific client
@app.post("/uploadJD")
async def upload_jd(
    file: UploadFile = File(...),
    client_name: str = Form(...)
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

    # Step 2: Upload the JD to the backend API
    upload_jd_url = f"{BACKEND_URL}/uploadJD"
    try:
        # Call the backend API to upload the JD
        jd_upload_response = requests.post(
            upload_jd_url,
            data={"client_name": client_name},
            files={"file": (file.filename, file.file)}
        )
        jd_upload_response.raise_for_status()
        return jd_upload_response.json()  # Return the upload response
    except requests.RequestException as e:
        logger.error(f"Error uploading JD for client {client_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload job description.")

# Run locally with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
