from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import mysql.connector
import uuid
from dotenv import load_dotenv
import uvicorn

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(root_path="/api/candidate-master")

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

# Database credentials from environment variables
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

# Define Pydantic models
class Candidate(BaseModel):
    cd_id: Optional[str] = None
    cd_first_name: str
    cd_last_name: Optional[str] = None
    cd_email: EmailStr
    cd_phno: str
    cd_qual: str
    cd_skills: Optional[str] = None
    cd_total_exp: int
    cd_related_exp: Optional[int] = None
    cd_loc: str
    cd_cur_ctc: float
    cd_exp_ctc: float
    cd_notice: str
    cd_work_mode: str
    cd_valid_passport: Optional[bool] = None
    created_by: Optional[str] = None
    rq_id: str 
    cl_id: Optional[str] = None 

class Requirement(BaseModel):
    rq_id: str
    rq_name: str
    cl_id: str 

class Client(BaseModel):
    cl_id: str
    cl_name: str

#1 Get all clients for dropdown
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

#2 Get requirements by client ID
@app.get("/requirements/{cl_id}", response_model=List[Requirement])
def get_requirements_by_client(cl_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT rq_id, rq_name, cl_id FROM requirements WHERE cl_id = %s", (cl_id,))
        requirements = cursor.fetchall()
        return requirements
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Failed to retrieve requirements.")
    finally:
        cursor.close()
        conn.close()

#3 Get all candidates with requirement and client info
@app.get("/candidates", response_model=List[Candidate])
def get_all_candidates():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT candidates.*, requirements.rq_name, requirements.cl_id
            FROM candidates
            JOIN requirements ON candidates.rq_id = requirements.rq_id
        """)
        candidates = cursor.fetchall()
        return candidates
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Failed to retrieve candidates.")
    finally:
        cursor.close()
        conn.close()

#4 Get candidates by requirement ID
@app.get("/candidates/requirement/{rq_id}", response_model=List[Candidate])
def get_candidates(rq_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT candidates.*, requirements.rq_name, requirements.cl_id
            FROM candidates
            JOIN requirements ON candidates.rq_id = requirements.rq_id
            WHERE candidates.rq_id = %s
        """, (rq_id,))
        candidates = cursor.fetchall()
        return candidates
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Failed to retrieve candidates.")
    finally:
        cursor.close()
        conn.close()

#5 Get a specific candidate by ID
@app.get("/candidates/{cd_id}", response_model=Candidate)
def get_candidate(cd_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT candidates.*, requirements.rq_name, requirements.cl_id
            FROM candidates
            JOIN requirements ON candidates.rq_id = requirements.rq_id
            WHERE candidates.cd_id = %s
        """, (cd_id,))
        candidate = cursor.fetchone()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found.")
        return candidate
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Failed to retrieve candidate.")
    finally:
        cursor.close()
        conn.close()


#6 Create a new candidate for a specific requirement
@app.post("/candidates/{rq_id}")
def create_candidate(rq_id: str, candidate: Candidate):
    candidate.cd_id = uuid.uuid4().hex  
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM requirements WHERE rq_id = %s", (rq_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Requirement not found.")
        
        
        cursor.execute("""
            INSERT INTO candidates (
                cd_id, rq_id, cd_first_name, cd_last_name, cd_email, cd_phno, cd_qual,
                cd_skills, cd_total_exp, cd_related_exp, cd_loc, cd_cur_ctc, cd_exp_ctc,
                cd_notice, cd_work_mode, cd_valid_passport, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            candidate.cd_id, rq_id, candidate.cd_first_name, candidate.cd_last_name or None, 
            candidate.cd_email, candidate.cd_phno, candidate.cd_qual, candidate.cd_skills or None, 
            candidate.cd_total_exp, candidate.cd_related_exp or None, candidate.cd_loc, 
            candidate.cd_cur_ctc, candidate.cd_exp_ctc, candidate.cd_notice, 
            candidate.cd_work_mode, candidate.cd_valid_passport, candidate.created_by or None
        ))

        conn.commit()
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to create candidate.")
    finally:
        cursor.close()
        conn.close()
    
    return {"message": "Candidate created successfully.", "candidate_id": candidate.cd_id}

#7 Update a candidate by ID
@app.put("/candidates/{cd_id}")
def update_candidate(cd_id: str, candidate: Candidate):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  
    try:
        
        cursor.execute("SELECT * FROM requirements WHERE rq_id = %s", (candidate.rq_id,))
        requirement = cursor.fetchone()  

        if not requirement:
            raise HTTPException(status_code=404, detail="Requirement not found.")

   
        cl_id = requirement['cl_id']  
        cursor.execute("""
            UPDATE candidates 
            SET cd_first_name = %s, cd_last_name = %s, cd_email = %s, cd_phno = %s,
            cd_qual = %s, cd_skills = %s, cd_total_exp = %s, cd_related_exp = %s, cd_loc = %s, cd_cur_ctc = %s,
            cd_exp_ctc = %s, cd_notice = %s, cd_work_mode = %s, cd_valid_passport = %s,
            created_by = %s, rq_id = %s
            WHERE cd_id = %s
        """, (
            candidate.cd_first_name, candidate.cd_last_name, candidate.cd_email, candidate.cd_phno,
            candidate.cd_qual, candidate.cd_skills, candidate.cd_total_exp, candidate.cd_related_exp, candidate.cd_loc,
            candidate.cd_cur_ctc, candidate.cd_exp_ctc, candidate.cd_notice, candidate.cd_work_mode,
            candidate.cd_valid_passport, candidate.created_by, candidate.rq_id, cd_id
        ))
        conn.commit()

    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to update candidate.")
    finally:
        cursor.close()
        conn.close()
    
    return {"message": "Candidate updated successfully."}


#8 Delete a candidate by ID
@app.delete("/candidates/{cd_id}")
def delete_candidate(cd_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM candidates WHERE cd_id = %s", (cd_id,))
        conn.commit()
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete candidate.")
    finally:
        cursor.close()
        conn.close()
    
    return {"message": "Candidate deleted successfully."}

if __name__ == "__main__":
    port = int(os.getenv("main", 8007)) 
    uvicorn.run(app, host="0.0.0.0", port=port)