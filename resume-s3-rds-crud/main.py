from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import boto3
import logging
import os
import mysql.connector
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(root_path="/api/resume_s3")

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

# MySQL credentials
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

# Initialize S3 client
s3_client = boto3.client('s3', 
                  aws_access_key_id=AWS_ACCESS_KEY, 
                  aws_secret_access_key=AWS_SECRET_KEY, 
                  region_name=AWS_REGION_NAME)

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
    return {"message": "Welcome to the Resume Upload API. Use the defined endpoints to interact with the service."}

# Upload file to S3 and return the S3 link
def upload_to_s3(file_content: bytes, file_name: str):
    try:
        s3_key = f"resumes/{file_name}"
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

# Function to delete from S3
def delete_from_s3(s3_link: str):
    try:
        s3_key = s3_link.split(f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_REGION_NAME}.amazonaws.com/")[-1]
        s3_client.delete_object(Bucket=AWS_S3_BUCKET_NAME, Key=s3_key)
        logger.info(f"Deleted {s3_key} from S3 bucket {AWS_S3_BUCKET_NAME}.")
    except Exception as e:
        logger.error(f"Failed to delete {s3_link} from S3: {e}")

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

# API to get job description filenames by client
@app.get("/jd_filenames_by_name/{client_name}")
def get_jd_filenames_by_name(client_name: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT HEX(client_id) as client_id FROM clients WHERE client_name = %s", (client_name,))
        client = cursor.fetchone()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")
        client_id = client['client_id']
        cursor.execute("SELECT filename FROM job_descriptions WHERE client_id = %s", (bytes.fromhex(client_id),))
        job_filenames = cursor.fetchall()
        return {
            "client_name": client_name,
            "jd_filenames": [jd['filename'] for jd in job_filenames]
        }
    except mysql.connector.Error as err:
        logger.error(f"Error fetching job filenames: {err}")
        raise HTTPException(status_code=500, detail="Failed to fetch job filenames.")
    finally:
        cursor.close()
        conn.close()

# API to upload a new resume
@app.post("/uploadResume")
async def upload_resume(
    client_name: str = Form(...),
    jd_filename: str = Form(...),
    file: UploadFile = File(...),
):
    file_content = await file.read()
    s3_link = None  # Initialize s3_link to None
    resume_id = uuid.uuid4().hex  # Unique resume ID

    try:
        # Upload to S3
        s3_link = upload_to_s3(file_content, file.filename)

        # Database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Get JD ID based on the JD filename
            cursor.execute("SELECT jd_id FROM job_descriptions WHERE filename = %s", (jd_filename,))
            jd_row = cursor.fetchone()
            if not jd_row:
                raise HTTPException(status_code=404, detail="JD not found.")
            jd_id = jd_row[0]

            # Insert resume metadata into the database
            cursor.execute(
                "INSERT INTO resumes (resume_id, jd_id, filename, s3_link) VALUES (%s, %s, %s, %s)",
                (resume_id, jd_id, file.filename, s3_link)
            )
            conn.commit()
            logger.info(f"Stored S3 link for {file.filename} with Resume ID {resume_id} in the database.")
        except mysql.connector.Error as err:
            logger.error(f"Error storing S3 link in DB: {err}")
            conn.rollback()  # Rollback the transaction
            delete_from_s3(s3_link)  # Delete from S3 if DB operation fails
            raise HTTPException(status_code=500, detail="Failed to store S3 link in the database.")
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"Error during upload process: {e}")
        if s3_link:  # If S3 upload was successful, delete it
            delete_from_s3(s3_link)
        raise HTTPException(status_code=500, detail="Failed to upload resume.")

    return {
        "message": f"{file.filename} uploaded to S3 and link stored in DB.",
        "s3_link": s3_link,
        "resume_id": resume_id
    }

# API to get all resumes
@app.get("/getAllResumes")
def get_all_resumes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT resume_id, jd_id, filename, s3_link, timestamp FROM resumes")
        resumes = cursor.fetchall()
        return resumes
    except mysql.connector.Error as err:
        logger.error(f"Error fetching resumes from DB: {err}")
        raise HTTPException(status_code=500, detail="Failed to fetch resumes from the database.")
    finally:
        cursor.close()
        conn.close()

# API to update a resume
@app.put("/resumes/{resume_id}")
async def update_resume(
    resume_id: str,
    jd_filename: str = Form(...),
    file: UploadFile = File(...)
):
    file_content = await file.read()
    s3_link = upload_to_s3(file_content, file.filename)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get JD ID based on the JD filename
        cursor.execute("SELECT jd_id FROM job_descriptions WHERE filename = %s", (jd_filename,))
        jd_row = cursor.fetchone()
        if not jd_row:
            raise HTTPException(status_code=404, detail="JD not found.")
        jd_id = jd_row[0]
        # Update resume metadata in the database
        cursor.execute(
            "UPDATE resumes SET jd_id = %s, filename = %s, s3_link = %s WHERE resume_id = %s",
            (jd_id, file.filename, s3_link, resume_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Resume not found.")
    except mysql.connector.Error as err:
        logger.error(f"Error updating resume: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to update resume.")
    finally:
        cursor.close()
        conn.close()
    return {
        "message": f"Resume {resume_id} updated successfully.",
        "s3_link": s3_link,
    }

# API to delete a resume
@app.delete("/resumes/{resume_id}")
def delete_resume(resume_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM resumes WHERE resume_id = %s", (resume_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Resume not found.")
        return {"detail": "Resume deleted successfully."}
    except mysql.connector.Error as err:
        logger.error(f"Error deleting resume: {err}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete resume.")
    finally:
        cursor.close()
        conn.close()
        
@app.get("/summary/counts")
def get_summary_counts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Query to get total counts without date filtering
        query = """
            SELECT 
                (SELECT COUNT(*) FROM clients) AS total_clients,
                (SELECT COUNT(*) FROM resumes) AS total_resumes,
                (SELECT COUNT(*) FROM job_descriptions) AS total_jds
        """
        
        cursor.execute(query)
        result = cursor.fetchone()

        return {
            "total_clients": result['total_clients'],
            "total_resumes": result['total_resumes'],
            "total_jds": result['total_jds']
        }
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database query failed: {err}")
    finally:
        cursor.close()
        conn.close()


# Run the application (only if this script is executed directly)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
