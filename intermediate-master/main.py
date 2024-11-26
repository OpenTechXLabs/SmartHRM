import os
import httpx
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from typing import List, Dict
import logging

# Define base backend URLs
BASE_BACKEND_URLS = {
    "clients": "http://client-master:8009/api/client-master",  # Client service
    "requirements": "http://requirement-master:8008/api/requirement-master",  # Requirement service
    "candidates": "http://candidate-master:8007/api/candidate-master",  # Candidate service
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intermediate_app = FastAPI(root_path="/api/intermediate-master")

async def forward_request(request: Request, method: str, category: str, backend_path: str):
    backend_url = BASE_BACKEND_URLS.get(category)
    if backend_url is None:
        raise HTTPException(status_code=404, detail="Backend service not found")

    url = f"{backend_url}{backend_path}"
    headers = dict(request.headers)

    logger.debug(f"Received {method} request with headers: {headers}")

    try:
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method in ["POST", "PUT"]:
                body = await request.body()
                if not body:
                    logger.error("Request body is empty")
                    raise HTTPException(status_code=400, detail="Empty request body")

                form_data = await request.json()
                logger.debug(f"Forwarding {method} request with data: {form_data}")

                if method == "POST":
                    response = await client.post(url, headers=headers, json=form_data)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=form_data)
            elif method == "DELETE":
                logger.debug(f"Forwarding DELETE request to {url}")
                response = await client.delete(url, headers=headers)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")

        response.raise_for_status()
        return response.json()
    
    except httpx.RequestError as exc:
        logger.error(f"An error occurred while requesting {exc.request.url!r}: {str(exc)}")
        raise HTTPException(status_code=500, detail="Failed to communicate with backend service")
    except httpx.HTTPStatusError as exc:
        logger.error(f"Received non-success status code {exc.response.status_code} from {exc.request.url!r}")
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)

@intermediate_app.get("/")
async def read_root():
    return {"message": "Intermediate API is running."}

# Clients CRUD Operations
@intermediate_app.get("/clients", response_model=List[Dict])
async def get_clients(request: Request):
    response = await forward_request(request, "GET", "clients", "/clients")
    return response

@intermediate_app.get("/clients/{client_id}", response_model=Dict)
async def get_client(request: Request, client_id: str):
    response = await forward_request(request, "GET", "clients", f"/clients/{client_id}")
    return response

@intermediate_app.post("/clients")
async def create_client(request: Request):
    response = await forward_request(request, "POST", "clients", "/clients")
    return response

@intermediate_app.put("/clients/{client_id}")
async def update_client(request: Request, client_id: str):
    response = await forward_request(request, "PUT", "clients", f"/clients/{client_id}")
    return response

@intermediate_app.delete("/clients/{client_id}")
async def delete_client(request: Request, client_id: str):
    response = await forward_request(request, "DELETE", "clients", f"/clients/{client_id}")
    return response

# 1. Get all requirements (GET)
@intermediate_app.get("/requirements", response_model=List[Dict])
async def get_requirements(request: Request):
    response = await forward_request(request, "GET", "requirements", "/requirements")
    return response

# 2. Get all requirements by client ID (GET)
@intermediate_app.get("/requirements/client/{cl_id}", response_model=List[Dict])
async def get_requirements_by_client(request: Request, cl_id: str):
    response = await forward_request(request, "GET", "requirements", f"/requirements/{cl_id}")
    return response

# 3. Get a single requirement by ID (GET)
@intermediate_app.get("/requirements/rq_id/{rq_id}", response_model=Dict)
async def get_requirement(request: Request, rq_id: str):
    response = await forward_request(request, "GET", "requirements", f"/requirements/rq_id/{rq_id}")
    return response

# 4. Create a new requirement for a specific client (POST)
@intermediate_app.post("/requirements/{cl_id}")
async def create_requirement_for_client(request: Request, cl_id: str):
    response = await forward_request(request, "POST", "requirements", f"/requirements/{cl_id}")
    return response

# 5. Update a requirement by ID (PUT)
@intermediate_app.put("/requirements/{rq_id}")
async def update_requirement(request: Request, rq_id: str):
    response = await forward_request(request, "PUT", "requirements", f"/requirements/{rq_id}")
    return response

# 6. Delete a requirement by ID (DELETE)
@intermediate_app.delete("/requirements/{rq_id}")
async def delete_requirement(request: Request, rq_id: str):
    response = await forward_request(request, "DELETE", "requirements", f"/requirements/{rq_id}")
    return response

# Candidates CRUD Operations
@intermediate_app.post("/candidates/{rq_id}")
async def create_candidate(request: Request, rq_id: str):
    response = await forward_request(request, "POST", "candidates", f"/candidates/{rq_id}")
    return response

@intermediate_app.get("/candidates", response_model=List[Dict])
async def get_candidates(request: Request):
    response = await forward_request(request, "GET", "candidates", "/candidates")
    return response

@intermediate_app.get("/candidates/{cd_id}", response_model=Dict)
async def get_candidate(request: Request, cd_id: str):
    response = await forward_request(request, "GET", "candidates", f"/candidates/{cd_id}")
    return response

@intermediate_app.put("/candidates/{cd_id}")
async def update_candidate(request: Request, cd_id: str):
    response = await forward_request(request, "PUT", "candidates", f"/candidates/{cd_id}")
    return response

@intermediate_app.delete("/candidates/{cd_id}")
async def delete_candidate(request: Request, cd_id: str):
    logger.info(f"Attempting to delete candidate with ID: {cd_id}")

    try:
        # Forward the DELETE request to the backend
        response = await forward_request(request, "DELETE", "candidates", f"/candidates/{cd_id}")

        # Log success message
        logger.info(f"Successfully deleted candidate with ID: {cd_id}")
        return response

    except HTTPException as e:
        # Log the error and re-raise it
        logger.error(f"Failed to delete candidate with ID {cd_id}: {e.detail}")
        raise e
    except Exception as e:
        # Log any unexpected errors
        logger.error(f"An unexpected error occurred while deleting candidate with ID {cd_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    port = int(os.getenv("INTERMEDIATE_API_PORT", 8011))  # Default to 8003 if not set
    uvicorn.run(intermediate_app, host="0.0.0.0", port=port)