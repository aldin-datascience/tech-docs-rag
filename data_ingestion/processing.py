from typing import List
from fastapi import UploadFile, HTTPException
from langchain_community.document_loaders import UnstructuredMarkdownLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import os
import re
from project_config.settings import TEMP_DIR
from project_config.logger import get_logger

# Initialize logger
logger = get_logger(__name__, log_file="document_processing.log")

os.makedirs(TEMP_DIR, exist_ok=True)


# Load a PDF document from an uploaded file
def load_pdf_doc_from_file(file: UploadFile) -> List[Document]:
    logger.info(f"Attempting to load PDF file: {file.filename}")
    if file.content_type != "application/pdf":
        logger.error(f"Invalid file type for {file.filename}. Expected 'application/pdf', got '{file.content_type}'.")
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    file_path = os.path.join(TEMP_DIR, file.filename)
    with open(file_path, "wb") as temp_file:
        temp_file.write(file.file.read())

    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        logger.info(f"Successfully loaded PDF file: {file.filename} with {len(documents)} documents.")
        return documents
    except Exception as e:
        logger.exception(f"Error loading PDF file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load PDF file: {str(e)}")
    finally:
        os.remove(file_path)
        logger.info(f"Temporary file {file_path} removed.")


# Load a Markdown document from an uploaded file
def load_markdown_doc_from_file(file: UploadFile) -> List[Document]:
    logger.info(f"Attempting to load Markdown file: {file.filename}")
    if file.content_type not in ["text/markdown", "text/plain"]:
        logger.error(
            f"Invalid file type for {file.filename}. Expected 'text/markdown' or 'text/plain', got '{file.content_type}'.")
        raise HTTPException(status_code=400, detail="File must be a Markdown or plain text file.")

    file_path = os.path.join(TEMP_DIR, file.filename)
    with open(file_path, "w", encoding="utf-8") as temp_file:
        temp_file.write(file.file.read().decode("utf-8"))

    try:
        loader = UnstructuredMarkdownLoader(file_path=file_path)
        documents = loader.load()
        logger.info(f"Successfully loaded Markdown file: {file.filename} with {len(documents)} documents.")
        return documents
    except Exception as e:
        logger.exception(f"Error loading Markdown file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load Markdown file: {str(e)}")
    finally:
        os.remove(file_path)
        logger.info(f"Temporary file {file_path} removed.")


# Chunk a single document
def chunk_document(doc: Document, chunk_size: int = 500, chunk_overlap: int = 50) -> List[Document]:
    logger.info(f"Chunking document with chunk size {chunk_size} and overlap {chunk_overlap}.")
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        chunks = text_splitter.split_documents([doc])
        logger.info(f"Document chunked into {len(chunks)} chunks.")
        return chunks
    except Exception as e:
        logger.exception(f"Error chunking document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to chunk document: {str(e)}")


# Replace newlines with spaces
def normalize_newlines(text: str) -> str:
    logger.debug("Normalizing newlines in text.")
    try:
        text = re.sub(r'\s*\n\s*', ' ', text)
        return text.strip()
    except Exception as e:
        logger.exception(f"Error normalizing newlines: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to normalize newlines.")


# Apply all the cleaning functions
def clean_document(doc: Document):
    logger.info(f"Cleaning document with metadata: {doc.metadata}")
    try:
        cleaned_doc = Document(page_content=normalize_newlines(doc.page_content), metadata=doc.metadata)
        logger.info("Document cleaned successfully.")
        return cleaned_doc
    except Exception as e:
        logger.exception(f"Error cleaning document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clean document.")
