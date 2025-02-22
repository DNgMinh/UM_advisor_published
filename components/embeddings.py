from langchain_community.embeddings import HuggingFaceEmbeddings
from typing import List

class EmbeddingsComponent:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.model_name
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        return self.embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query text."""
        return self.embeddings.embed_query(text)