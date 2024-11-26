from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import mysql.connector
import uuid
from dotenv import load_dotenv
from pydantic import BaseModel
import uvicorn
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(root_path="/api/client-master")

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

# MySQL environment variables
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

# Define a Pydantic model for the contact data
class Contact(BaseModel):
    co_id: Optional[str] = None  
    co_name: str
    co_position_hr: Optional[str] = None
    co_email: str
    co_phno: str

# Define a Pydantic model for the client data
class ClientWithContacts(BaseModel):
    cl_id: Optional[str] = None 
    cl_name: str
    cl_email: Optional[str] = None
    cl_phno: Optional[str] = None
    cl_addr: Optional[str] = None
    cl_map_url: Optional[str] = None
    cl_type: Optional[str] = None
    cl_notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    contacts: List[Contact] = []

# 1. Create a new client with multiple contacts (POST)
@app.post("/clients")
def create_client_with_contacts(client: ClientWithContacts):
    cl_uuid = uuid.uuid4() 
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert client data
        cursor.execute(
            "INSERT INTO clients (cl_id, cl_name, cl_email, cl_phno, cl_addr, cl_map_url, cl_type, cl_notes, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (cl_uuid.hex, client.cl_name, client.cl_email, client.cl_phno, client.cl_addr, client.cl_map_url, client.cl_type, client.cl_notes, client.created_by)
        )
        # Insert contact data for each contact in the list
        for contact in client.contacts:
            co_uuid = uuid.uuid4()  
            cursor.execute(
                "INSERT INTO contacts (co_id, co_name, co_position_hr, co_email, co_phno, cl_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (co_uuid.hex, contact.co_name, contact.co_position_hr, contact.co_email, contact.co_phno, cl_uuid.hex)
            )
        conn.commit()
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to create client and contacts.")
    finally:
        cursor.close()
        conn.close()
    return {"message": "Client and contacts created successfully.", "client_id": cl_uuid.hex}

# 2. Read all clients (GET)
@app.get("/clients", response_model=List[ClientWithContacts])
def get_clients():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM clients")
        clients = cursor.fetchall()
        client_list = []
        for client in clients:
            cursor.execute("SELECT * FROM contacts WHERE cl_id = %s", (client['cl_id'],))
            contacts = cursor.fetchall()
            client['contacts'] = contacts
            client_list.append(client)
        return client_list
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Failed to retrieve clients.")
    finally:
        cursor.close()
        conn.close()

# 3. Read a specific client by ID (GET)
@app.get("/clients/{client_id}", response_model=ClientWithContacts)
def get_client(client_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM clients WHERE cl_id = %s", (client_id,))
        client = cursor.fetchone()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")
        cursor.execute("SELECT * FROM contacts WHERE cl_id = %s", (client_id,))
        contacts = cursor.fetchall()
        client['contacts'] = contacts
        return client
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Failed to retrieve client.")
    finally:
        cursor.close()
        conn.close()

# 4. Update a client by ID (PUT)
@app.put("/clients/{client_id}")
def update_client(client_id: str, client: ClientWithContacts):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE clients SET cl_name = %s, cl_email = %s, cl_phno = %s, cl_addr = %s, cl_map_url = %s, cl_type = %s, cl_notes = %s, created_by = %s WHERE cl_id = %s",
            (client.cl_name, client.cl_email, client.cl_phno, client.cl_addr, client.cl_map_url, client.cl_type, client.cl_notes, client.created_by, client_id)
        )
        # Clear existing contacts for the client
        cursor.execute("DELETE FROM contacts WHERE cl_id = %s", (client_id,))
        # Insert updated contacts
        for contact in client.contacts:
            co_uuid = uuid.uuid4() 
            cursor.execute(
                "INSERT INTO contacts (co_id, co_name, co_position_hr, co_email, co_phno, cl_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (co_uuid.hex, contact.co_name, contact.co_position_hr, contact.co_email, contact.co_phno, client_id)
            )
        conn.commit()
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to update client.")
    finally:
        cursor.close()
        conn.close()
    return {"message": "Client updated successfully."}

# 5. Delete a client by ID (DELETE)
@app.delete("/clients/{client_id}")
def delete_client(client_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Delete contacts for the client
        cursor.execute("DELETE FROM contacts WHERE cl_id = %s", (client_id,))
        # Delete the client
        cursor.execute("DELETE FROM clients WHERE cl_id = %s", (client_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Client not found.")
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete client.")
    finally:
        cursor.close()
        conn.close()
    return {"message": "Client deleted successfully."}

if __name__ == "__main__":
    port = int(os.getenv("main", 8009)) 
    uvicorn.run(app, host="0.0.0.0", port=port)

