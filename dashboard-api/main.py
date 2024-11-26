from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(root_path="/api/dashboard")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MySQL credentials
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

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
        raise HTTPException(status_code=500, detail="Database connection failed.")

@app.get("/summary/counts")
def get_summary_counts(
    start_date: str = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(None, description="End date in YYYY-MM-DD format")
):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Validate date formats
    if start_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start date format. Use YYYY-MM-DD.")

    if end_date:
        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end date format. Use YYYY-MM-DD.")

    try:
        # Query to get total counts with date filtering
        query = """
            SELECT 
                (SELECT COUNT(*) FROM clients WHERE created_at >= %s AND (%s IS NULL OR created_at <= %s)) AS total_clients,
                (SELECT COUNT(*) FROM resumes WHERE timestamp >= %s AND (%s IS NULL OR timestamp <= %s)) AS total_resumes,
                (SELECT COUNT(*) FROM job_descriptions WHERE created_at >= %s AND (%s IS NULL OR created_at <= %s)) AS total_jds
        """
        
        cursor.execute(query, (start_date, start_date, end_date, start_date, start_date, end_date, start_date, start_date, end_date))
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
    uvicorn.run(app, host="0.0.0.0", port=8005)  # Adjust the port as necessary
