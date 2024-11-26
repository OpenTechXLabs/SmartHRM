from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from chains import SQLChain

# Load environment variables from .env file (optional)
load_dotenv()

# Initialize FastAPI app
app = FastAPI(root_path="/api/ai-assistant")

# Add CORS middleware (for frontend testing, allows requests from any origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chain = SQLChain()

@app.get("/query")
def query(question: str):
    try:
        response = chain.invoke(question)
        if "Error" in response:
            raise HTTPException(status_code=500, detail=response["Error"])
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# @app.get("/model")
# def model_test():
    
#     return model
    