from fastapi import FastAPI, UploadFile, HTTPException, Depends
from data_ingestion.processing import load_pdf_doc_from_file, load_markdown_doc_from_file
import os
import shutil
from pydantic import BaseModel
from data_ingestion.vespa_utils import save_to_vespa, clean_database, is_vespa_healthy
from project_config.logger import get_logger
from project_config.settings import TEMP_DIR
from src.chatbot.chatbot import Chatbot
from src.api.auth import simple_auth

app = FastAPI()
os.makedirs(TEMP_DIR, exist_ok=True)
logger = get_logger(__name__, log_file="fastapi.log")

# a single global chatbot instance
chatbot = Chatbot()

class QueryPayload(BaseModel):
    session_id: str
    question: str

# FastAPI endpoint to process an uploaded file
@app.post("/process-file/")
async def process_file(file: UploadFile, authorized: bool = Depends(simple_auth)):
    """
    Endpoint to process file uploads and store their contents in the Vespa database.

    This endpoint accepts a single file via form-data. Supported file types include:
      - application/pdf
      - text/markdown
      - text/plain

    **Request Body**
    - `file`: The file to be uploaded. Must be one of the supported MIME types.

    **Response**
    - **200**:
      Returns a JSON object with a success message, e.g.:
      `{"message": "File my_file.pdf processed successfully."}`
    - **400**:
      Raised if the file type is unsupported or if the document content cannot be loaded.
    - **500**:
      Raised if any error occurs during processing or saving the file to Vespa.
    """
    logger.info(f"Received file upload request: {file.filename} with content type: {file.content_type}")

    try:
        # Determine file type and process accordingly
        if file.content_type == "application/pdf":
            docs = load_pdf_doc_from_file(file)
            logger.info(f"Processed PDF file: {file.filename}")
        elif file.content_type in ["text/markdown"]:
            docs = load_markdown_doc_from_file(file)
            logger.info(f"Processed Markdown file: {file.filename}")
        else:
            logger.error(f"Unsupported file type: {file.content_type}")
            raise HTTPException(status_code=400, detail="Unsupported file type.")

        if not docs:
            logger.error(f"Failed to load document content for file: {file.filename}")
            raise HTTPException(status_code=400, detail="Failed to load document content.")

        # Save both the resource and its chunks into Vespa
        for doc in docs:
            save_to_vespa(resource=doc, resource_type=file.content_type)

        logger.info(f"Successfully saved {file.filename} to Vespa database.")

        return {
            "message": f"File {file.filename} processed successfully.",
        }
    except Exception as e:
        logger.exception(f"Error processing file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/process-query/")
async def process_query(payload: QueryPayload, authorized: bool = Depends(simple_auth)):
    """
    Endpoint to process user queries and return answers from the chatbot.

    Request Body:
    {
        "session_id": "<session ID>",
        "question": "<the user's question>"
    }

    Response:
    {
        "answer": "<the chatbot's answer>"
    }
    """
    try:
        # Get the answer from the chatbot
        answer = chatbot.get_answer(
            question=payload.question,
            session_id=payload.session_id
        )
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clean-memory/")
async def clean_memory(authorized: bool = Depends(simple_auth)):
    """
    Endpoint to clean the Vespa database by deleting all resources and chunks.
    """
    logger.info("Received request to clean Vespa database.")
    try:
        clean_database()
        logger.info("Database cleaned successfully.")
        return {"message": "Database cleaned successfully."}
    except Exception as e:
        logger.exception(f"Failed to clean database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clean database: {str(e)}")

# Cleanup function to remove the temporary directory
@app.on_event("shutdown")
def cleanup_temp_dir():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)


@app.get("/health/api-health")
async def api_health_check(authorized: bool = Depends(simple_auth)):
    """
    Liveness check endpoint.

    This endpoint returns a 200 status code if the service is running.

    **Response**
    - **200**: Service is alive.
    """
    return {"status": "API is alive"}


@app.get("/health/dependencies-health")
async def vespa_health_check(authorized: bool = Depends(simple_auth)):
    """
    Readiness check endpoint.

    This endpoint attempts to verify that dependencies e.g. Vespa is ready to handle requests.
    If a query fails, a 503 status code is returned, indicating that the API
    is not ready to handle requests.

    **Response**
    - **200**: All dependencies are ready; service can handle requests.
    - **503**: One of the dependencies is not responding, or another critical error occurred.
    """
    try:
        # Check if Vespa is healthy
        if not is_vespa_healthy():
            raise Exception("Vespa is not ready")

        return {"status": "All dependencies are ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))