from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import boto3
import logging
import os
import mysql.connector
import uuid
from dotenv import load_dotenv
import io

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(root_path="/api/jd_s3")

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

# AWS credentials
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_REGION_NAME = os.getenv("AWS_REGION_NAME")
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

# Initialize S3 client
s3_client = boto3.client(
    's3',
    region_name=AWS_REGION_NAME,

)

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

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the API. Use the defined endpoints to interact with the service."}

# Upload JD to S3 and return S3 link
def upload_to_s3(file_content: bytes, file_name: str):
    try:
        s3_key = f"JD/{file_name}"
        s3_client.put_object(
            Bucket=AWS_S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content
        )
        s3_link = f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_REGION_NAME}.amazonaws.com/{s3_key}"
        logger.info(f"Uploaded {file_name} to S3 bucket {AWS_S3_BUCKET_NAME} at {s3_key}")
        return s3_link
    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")
        raise HTTPException(status_code=500, detail="Error uploading to S3.")

# Generate JD ID
def generate_jd_id(client_name: str, filename: str, conn):
    base_name = (client_name.replace(" ", "")[:3] + filename.replace(" ", "")[:3]).lower()
    incremental_number = 1
    
    while True:
        jd_id = f"{base_name}{incremental_number:03d}"
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM job_descriptions WHERE jd_id = %s", (jd_id,))
        count = cursor.fetchone()[0]
        cursor.close()
        
        if count == 0:
            return jd_id
        incremental_number += 1

# API to create a new client
@app.post("/clients")
def create_client(client_name: str):
    client_uuid = uuid.uuid4()  # Create a UUID object
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if the client name already exists before inserting
        cursor.execute("SELECT COUNT(*) FROM clients WHERE client_name = %s", (client_name,))
        if cursor.fetchone()[0] > 0:
            raise HTTPException(status_code=400, detail="Client name must be unique.")

        cursor.execute("INSERT INTO clients (client_id, client_name) VALUES (%s, %s)", (client_uuid.bytes, client_name))
        conn.commit()
        return {"client_id": client_uuid.hex, "client_name": client_name}  # Use hex to return a string representation
    except mysql.connector.Error as err:
        logger.error(f"Error creating client: {err}")
        conn.rollback()
        
        # Check for unique constraint violation
        if err.errno == mysql.connector.errorcode.ER_DUP_ENTRY:
            raise HTTPException(status_code=400, detail="Client name must be unique.")
        
        raise HTTPException(status_code=500, detail="Failed to create client.")
    finally:
        cursor.close()
        conn.close()

# API to get all clients
@app.get("/clients")
def get_clients():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT HEX(client_id) as client_id, client_name FROM clients")
        clients = cursor.fetchall()
        return clients
    except mysql.connector.Error as err:
        logger.error(f"Error fetching clients: {err}")
        raise HTTPException(status_code=500, detail="Failed to fetch clients.")
    finally:
        cursor.close()
        conn.close()

# API to update a client
@app.put("/clients/{client_id}")
def update_client(client_id: str, client_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE clients SET client_name = %s WHERE client_id = %s", (client_name, bytes.fromhex(client_id)))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Client not found.")
        return {"client_id": client_id, "client_name": client_name}
    except mysql.connector.Error as err:
        logger.error(f"Error updating client: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to update client.")
    finally:
        cursor.close()
        conn.close()

# API to delete a client
@app.delete("/clients/{client_id}")
def delete_client(client_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM clients WHERE client_id = %s", (bytes.fromhex(client_id),))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Client not found.")
        return {"detail": "Client deleted successfully."}
    except mysql.connector.Error as err:
        logger.error(f"Error deleting client: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete client.")
    finally:
        cursor.close()
        conn.close()

# API to upload JD and store S3 link and client name in the database
@app.post("/uploadJD")
async def upload(client_name: str = Form(...), file: UploadFile = File(...)):
    file_content = await file.read()
    s3_link = upload_to_s3(file_content, file.filename)

    # Get the filename without the extension
    filename_without_extension = os.path.splitext(file.filename)[0]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if the client exists by name
        cursor.execute("SELECT client_id FROM clients WHERE client_name = %s", (client_name,))
        client_row = cursor.fetchone()

        if not client_row:
            raise HTTPException(status_code=404, detail="Client not found.")

        client_id = client_row[0]

        # Generate JD ID
        jd_id = generate_jd_id(client_name, filename_without_extension, conn)

        # Insert job description into the database
        cursor.execute(
            "INSERT INTO job_descriptions (jd_id, client_id, filename, s3_link) VALUES (%s, %s, %s, %s)",
            (jd_id, client_id, file.filename, s3_link)
        )
        conn.commit()
        logger.info(f"Stored S3 link for {filename_without_extension} with JD ID {jd_id} in the database.")

    except mysql.connector.Error as err:
        logger.error(f"Error storing S3 link in DB: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to store S3 link in the database.")
    finally:
        cursor.close()
        conn.close()

    return {
        "message": f"{file.filename} uploaded to S3 and link stored in DB.",
        "s3_link": s3_link,
        "jd_id": jd_id
    }

# API to get all job descriptions
@app.get("/getAllJDs")
def get_all_jds():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT jd_id, HEX(client_id) as client_id, filename, s3_link, timestamp FROM job_descriptions")
        job_descriptions = cursor.fetchall()
        return job_descriptions
    except mysql.connector.Error as err:
        logger.error(f"Error fetching JD links from DB: {err}")
        raise HTTPException(status_code=500, detail="Failed to fetch JD links from the database.")
    finally:
        cursor.close()
        conn.close()

# API to update a job description
@app.put("/jds/{jd_id}")
def update_jd(jd_id: str, client_id: str = Form(...), filename: str = Form(...), s3_link: str = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE job_descriptions SET client_id = %s, filename = %s, s3_link = %s WHERE jd_id = %s",
            (bytes.fromhex(client_id), filename, s3_link, jd_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Job description not found.")
        return {"jd_id": jd_id, "client_id": client_id, "filename": filename, "s3_link": s3_link}
    except mysql.connector.Error as err:
        logger.error(f"Error updating job description: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to update job description.")
    finally:
        cursor.close()
        conn.close()

# API to delete a job description
@app.delete("/jds/{jd_id}")
def delete_jd(jd_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM job_descriptions WHERE jd_id = %s", (jd_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Job description not found.")
        return {"detail": "Job description deleted successfully."}
    except mysql.connector.Error as err:
        logger.error(f"Error deleting job description: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete job description.")
    finally:
        cursor.close()
        conn.close()

# Run the application (only if this script is executed directly)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
