from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import mysql.connector
import uuid
from dotenv import load_dotenv
from pydantic import BaseModel
from datetime import date
import uvicorn
from typing import Union

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(root_path="/api/requirement-master")

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

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

# MySQL connection function
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Database connection failed.")

# Define Pydantic model for Requirement
class Requirement(BaseModel):
    rq_id: str
    cl_id: str 
    rq_name: str
    rq_loc: str
    rq_map_url: Optional[str] = None
    rq_no_pos: int
    rq_qual: Optional[str] = None
    rq_skills: str
    rq_exp: int
    rq_budget: Optional[float] = None
    rq_work_mode: Optional[str] = None
    rq_start_date: Optional[date] = None
    rq_no_of_days: Optional[Union[int, str]] = None  
    rq_notes: Optional[str] = None
    created_by: Optional[str] = None

# Define Pydantic model for Client (for dropdown)
class Client(BaseModel):
    cl_id: str
    cl_name: str

# 1. Get all clients for dropdown (GET)
@app.get("/clients", response_model=List[Client])
def get_clients():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT cl_id, cl_name FROM clients")
        clients = cursor.fetchall()
        return clients
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Failed to retrieve clients.")
    finally:
        cursor.close()
        conn.close()

# 2. Create a new requirement for a specific client (POST)
@app.post("/requirements/{cl_id}")
def create_requirement_by_client(cl_id: str, requirement: Requirement):
    rq_uuid = uuid.uuid4()  # Generate UUID for the new requirement
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Ensure the client exists before creating the requirement
        cursor.execute("SELECT * FROM clients WHERE cl_id = %s", (cl_id,))
        client = cursor.fetchone()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")
        
        # Insert the new requirement with the provided cl_id
        cursor.execute(
            """INSERT INTO requirements (rq_id, cl_id, rq_name, rq_loc, rq_map_url, rq_no_pos, rq_qual, 
               rq_skills, rq_exp, rq_budget, rq_work_mode, rq_start_date, rq_no_of_days, rq_notes, created_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (rq_uuid.hex, cl_id, requirement.rq_name, requirement.rq_loc, requirement.rq_map_url,
             requirement.rq_no_pos, requirement.rq_qual, requirement.rq_skills, requirement.rq_exp,
             requirement.rq_budget, requirement.rq_work_mode, requirement.rq_start_date,
             requirement.rq_no_of_days, requirement.rq_notes, requirement.created_by)
        )
        conn.commit()
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to create requirement.")
    finally:
        cursor.close()
        conn.close()
    
    return {"message": "Requirement created successfully.", "requirement_id": rq_uuid.hex}

# 3. Read all requirements (GET)
@app.get("/requirements", response_model=List[Requirement])
def get_requirements():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM requirements")
        requirements = cursor.fetchall()
        return requirements
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Failed to retrieve requirements.")
    finally:
        cursor.close()
        conn.close()

# 4. Read all requirements by client ID (GET)
@app.get("/requirements/{cl_id}", response_model=List[Requirement])
def get_requirement(cl_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Query to fetch requirements based on the client ID (cl_id)
        cursor.execute("SELECT * FROM requirements WHERE cl_id = %s", (cl_id,))
        requirements = cursor.fetchall()
        
        if not requirements:
            raise HTTPException(status_code=404, detail="No requirements found for the given client ID.")
        
        return requirements
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Failed to retrieve requirements.")
    finally:
        cursor.close()
        conn.close()

# 5. Read a single requirement by rq_id (GET)
@app.get("/requirements/rq_id/{rq_id}", response_model=Requirement)
def get_requirement_by_id(rq_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM requirements WHERE rq_id = %s", (rq_id,))
        requirement = cursor.fetchone()
        
        if not requirement:
            raise HTTPException(status_code=404, detail="Requirement not found.")
        
        return requirement
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Failed to retrieve requirement.")
    finally:
        cursor.close()
        conn.close()

# 6. Update a requirement by ID (PUT)
@app.put("/requirements/{rq_id}")
def update_requirement(rq_id: str, requirement: Requirement):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Update the requirement, including cl_id if it has changed
        cursor.execute(
            """UPDATE requirements SET cl_id = %s, rq_name = %s, rq_loc = %s, rq_map_url = %s, rq_no_pos = %s, 
               rq_qual = %s, rq_skills = %s, rq_exp = %s, rq_budget = %s, rq_work_mode = %s, 
               rq_start_date = %s, rq_no_of_days = %s, rq_notes = %s, created_by = %s 
               WHERE rq_id = %s""",
            (requirement.cl_id, requirement.rq_name, requirement.rq_loc, requirement.rq_map_url, requirement.rq_no_pos, 
             requirement.rq_qual, requirement.rq_skills, requirement.rq_exp, requirement.rq_budget, 
             requirement.rq_work_mode, requirement.rq_start_date, requirement.rq_no_of_days, 
             requirement.rq_notes, requirement.created_by, rq_id)
        )
        conn.commit()
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to update requirement.")
    finally:
        cursor.close()
        conn.close()
    
    return {"message": "Requirement updated successfully.", "requirement_id": rq_id}

# 7. Delete a requirement by ID (DELETE)
@app.delete("/requirements/{rq_id}")
def delete_requirement(rq_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM requirements WHERE rq_id = %s", (rq_id,))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Requirement not found.")

    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete requirement.")
    finally:
        cursor.close()
        conn.close()

    return {"message": "Requirement deleted successfully."}

if __name__ == "__main__":
    port = int(os.getenv("main", 8008)) 
    uvicorn.run(app, host="0.0.0.0", port=port)
