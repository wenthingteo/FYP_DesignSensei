import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """
    Get the embedding of a text using OpenAI embedding models.
    
    Args:
        text (str): The input text to embed.
        model (str): The embedding model to use. Default is text-embedding-3-small.
    
    Returns:
        List[float]: The embedding vector.
    """
    try:
        response = openai.embeddings.create(
            model=model,
            input=text
        )
        embedding = response.data[0].embedding
        return embedding
    except Exception as e:
        print(f"Embedding failed: {e}")
        return []
