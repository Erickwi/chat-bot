from qdrant_client import QdrantClient, models

qdrant_client = QdrantClient(
    url="https://a063d286-b561-49d2-b857-141de9938c15.us-east4-0.gcp.cloud.qdrant.io:6333", 
    api_key="BbWYd5Q9BULpgozU8Lf1UXmpuY9e5LyJ0zABUw0apRhQKYNFLYRUiQ",
)

qdrant_client.create_collection(
    collection_name="chat_bot_universidad",
    vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
)

print(qdrant_client.get_collections())