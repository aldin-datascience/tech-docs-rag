import hashlib
from data_ingestion.processing import clean_document, chunk_document
from vespa_config.vespa_client import VespaClient
from project_config.settings import VESPA_HOST, VESPA_PORT
from data_ingestion.embedder import Embedder
from langchain.schema import Document
from project_config.logger import get_logger

logger = get_logger(__name__, log_file="vespa_operations.log")

vespa_client = VespaClient(vespa_host=VESPA_HOST, vespa_port=VESPA_PORT)
embedder = Embedder()


def generate_deterministic_id(content: str) -> str:
    """
    Generate a deterministic ID based on the content.
    :param content: Content to hash.
    :return: A unique ID for the content.
    """
    logger.debug("Generating deterministic ID for content.")
    try:
        content_id = hashlib.md5(content.encode("utf-8")).hexdigest()
        logger.debug(f"Generated ID: {content_id}")
        return content_id
    except Exception as e:
        logger.exception("Error generating deterministic ID.")
        raise e


def save_to_vespa(resource: Document, resource_type: str):
    """
    Saves a resource and its chunks into the Vespa vector database.

    :param resource_type: Type of resource e.g. text/markdown.
    :param resource: The main resource document to save.
    """
    try:
        logger.info(f"Saving resource of type {resource_type} to Vespa.")

        # Generate a deterministic resource_id
        resource_id = generate_deterministic_id(resource.page_content)
        logger.debug(f"Generated resource ID: {resource_id}")

        clean_resource = None
        if resource_type == "application/pdf":
            clean_resource = clean_document(resource)
            resource_embedding = embedder.openai_embedding(clean_resource.page_content)
            logger.info("Cleaned resource content.")
        else:
            resource_embedding = embedder.openai_embedding(resource.page_content)

        logger.info("Generated embedding for resource.")

        # Prepare resource record for insertion
        resource_record = {
            "id": resource_id,
            "fields": {
                "resource_id": resource_id,
                "resource_type": resource_type,
                "raw_text": resource.page_content,
                "cleaned_text": clean_resource.page_content if clean_resource else resource.page_content,
                "embedding": resource_embedding,
            }
        }

        # Insert the resource into the Vespa database
        vespa_client.insert_one("resources", resource_record)
        logger.info(f"Resource with ID {resource_id} inserted into Vespa.")

        # Process and insert chunks
        chunks = chunk_document(clean_resource if clean_resource else resource, resource_type)
        chunk_records = []

        for idx, chunk in enumerate(chunks):
            chunk_id = generate_deterministic_id(f"{resource_id}-{chunk.page_content}")
            chunk_embedding = embedder.openai_embedding(chunk.page_content)
            chunk_record = {
                "id": chunk_id,
                "fields": {
                    "chunk_id": chunk_id,
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                    "chunk_text": chunk.page_content,
                    "chunk_ordinal": idx,
                    "embedding": chunk_embedding,
                }
            }
            chunk_records.append(chunk_record)

        vespa_client.insert_many("chunks", chunk_records)
        logger.info(f"Inserted {len(chunk_records)} chunks for resource ID {resource_id}.")
    except Exception as e:
        logger.exception(f"Failed to save resource to Vespa: {str(e)}")
        raise e


def clean_database():
    """
    Cleans the Vespa database by deleting all resources and chunks.
    """
    logger.info("Starting database cleanup process.")

    def delete_items(index_name, id_field):
        """
        Helper function to query and delete items from a Vespa index.

        :param index_name: The name of the index (e.g., 'resources', 'chunks').
        :param id_field: The field name representing the unique ID (e.g., 'resource_id', 'chunk_id').
        """
        try:
            logger.info(f"Querying items from {index_name} for deletion.")
            items = vespa_client.query({
                'yql': f'select * from {index_name} where true'
            })

            ids_to_delete = [item['fields'][id_field] for item in items]

            if ids_to_delete:
                vespa_client.delete_many(index_name, ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} items from {index_name}.")
            else:
                logger.info(f"No items to delete in {index_name}.")
        except Exception as e:
            logger.exception(f"Error deleting items from {index_name}: {str(e)}")
            raise e

    try:
        delete_items("resources", "resource_id")
        delete_items("chunks", "chunk_id")
        logger.info("Database cleanup completed successfully.")
    except Exception as e:
        logger.exception(f"Database cleanup failed: {str(e)}")
        raise e

def is_vespa_healthy() -> bool:
    """
    Check Vespa's health by performing a simple query.

    Returns:
        bool: True if Vespa can be queried successfully, False otherwise.
    """
    try:
        # Perform a minimal query (e.g., limit to 1 result from the 'resources' index)
        _ = vespa_client.query({
            "yql": "select * from resources where true limit 1"
        })
        return True
    except Exception as e:
        logger.exception("Vespa health check failed.")
        return False
