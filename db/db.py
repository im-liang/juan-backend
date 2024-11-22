import os

from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential


COSMOS_DB_URI = os.environ['ACCOUNT_URI']
KEY = os.environ['ACCOUNT_KEY']
DATABASE_NAME = "LeetCodeSharing"
CONTAINER_NAME = "User"

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
    query = "SELECT DISTINCT c.leetcode_username FROM c WHERE IS_DEFINED(c.leetcode_username)"
    return list(container.query_items(query=query, enable_cross_partition_query=True))

def get_user_by_email(email):
    query = f"SELECT * FROM c WHERE c.email='{email}'"
    return list(container.query_items(query=query, enable_cross_partition_query=True))

def insert_user(data):
    """Insert a new submission into the Cosmos DB container."""
    operation_response = container.create_item(body=data)
    print(operation_response)
