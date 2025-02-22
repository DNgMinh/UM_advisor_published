from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter

from typing import List, Dict, Any
from langchain_core.documents import Document

class TextSplitterComponent:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # self.text_splitter = CharacterTextSplitter(
        #     chunk_size=self.chunk_size,
        #     chunk_overlap=self.chunk_overlap
        # )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            # separators=["\n\n", ".", "\n"]
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        # return self.text_splitter.split_documents(documents)
    
        split_docs = []
        # doc_pages = []

        for i, doc in enumerate(documents, 1):
            text_chunks = self.text_splitter.split_text(doc.page_content)  # Correctly splits text
            # print(f"Page has {len(text_chunks)} chunks")  # Debugging
            # doc_pages.append(Document(page_content=doc.page_content, page_number=i))

            # add (extend) the list of 1 page to split_docs
            # split_docs.extend([Document(page_content=chunk, metadata={**doc.metadata, 'page_number': i, 'full_page_content': doc.page_content}) for chunk in text_chunks])
            split_docs.extend([Document(page_content=chunk, metadata={**doc.metadata, 'page_number': i}) for chunk in text_chunks])

        return split_docs

    def split_text(self, text: str) -> List[Document]:
        """Split a single text into chunks."""
        return self.text_splitter.create_documents([text])