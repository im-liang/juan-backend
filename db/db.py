import os
import logging

from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential


COSMOS_DB_URI = os.environ['ACCOUNT_URI']
KEY = os.environ['ACCOUNT_KEY']
DATABASE_NAME = "LeetCodeSharing"
CONTAINER_NAME = "User"

logger = logging.getLogger("db")

# Initialize the Cosmos DB client
client = CosmosClient(COSMOS_DB_URI, credential=KEY)
database = client.create_database_if_not_exists(DATABASE_NAME)
container = database.create_container_if_not_exists(
    id=CONTAINER_NAME,
    partition_key=PartitionKey(path="/username"),
    offer_throughput=400
)

def get_all_users():
    """Retrieve all users from the Cosmos DB container."""
    query = "SELECT DISTINCT c.leetcode_username FROM c WHERE IS_DEFINED(c.leetcode_username) AND c.leetcode_username != '' AND LENGTH(c.leetcode_username) > 0 AND c.leetcode_username != 'None' AND c.share_submission = true"
    return list(container.query_items(query=query, enable_cross_partition_query=True))

def get_user_by_email(email):
    query = f"SELECT * FROM c WHERE c.email='{email}'"
    results = list(container.query_items(query=query, enable_cross_partition_query=True))

    if results:
        return results[0]
    return None

def insert_user(data):
    """Insert a new submission into the Cosmos DB container."""
    operation_response = container.create_item(body=data)
    logger.info(f"Inserted user: {operation_response}")

def update_user_details(email, new_username=None, share_submission=None):
    """
    Update the leetcode_username and/or share_submission flag for a user identified by their email.

    :param email: The email of the user to update.
    :param new_username: The new leetcode_username to set (optional).
    :param share_submission: The new value for share_submission (optional).
    :return: The updated document, or None if the user was not found.
    """
    try:
        # Retrieve the user by email
        query = "SELECT * FROM c WHERE c.email=@Email"
        parameters = [{"name": "@Email", "value": email}]
        user_documents = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        if not user_documents:
            logger.warning(f"No user found with email: {email}")
            return None
        
        # Assume email is unique, so get the first result
        user_document = user_documents[0]

        # Update the fields if new values are provided
        if new_username is not None:
            user_document["leetcode_username"] = new_username
        if share_submission is not None:
            user_document["share_submission"] = share_submission

        # Replace the item in the database
        updated_document = container.replace_item(item=user_document["id"], body=user_document)
        logger.info(f"Updated details for user with email {email}.")
        return updated_document
    except Exception as e:
        logger.error(f"Error updating user details for email {email}: {e}")
