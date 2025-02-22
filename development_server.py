from langchain_community.document_loaders import PyPDFLoader
from components.text_splitter import TextSplitterComponent
from components.embeddings import EmbeddingsComponent
from components.vectorstore import SQLiteVectorStore
from components.Gemini_call import GeminiService
from components.pagestore import SQLitePageStore
from components.crawl_intelliresponse import IntelliresponseCrawler
import os

def list_pdfs(directory: str) -> list[str]:
    """List all PDF files in the given directory."""
    return [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]

def process_pdf(pdf_path: str, text_splitter: TextSplitterComponent, 
                vectorstore: SQLiteVectorStore, pagestore: SQLitePageStore, force_reindex: bool = False) -> None:
    """Process a single PDF file."""
    print(f"\nProcessing {pdf_path}...")
    
    if vectorstore.is_file_indexed(pdf_path) and not force_reindex:
        print(f"File {pdf_path} is already indexed. Skipping...")
        return
        
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    print("Splitting text into chunks...")
    texts = text_splitter.split_documents(documents)
    print(f"Created {len(texts)} text chunks")
    
    print("Adding documents to vector store...")
    vectorstore.add_documents(texts, source_file=pdf_path, force_reindex=force_reindex)

    print("Adding documents to page store...")
    # vectorstore.add_documents(texts, source_file=pdf_path, force_reindex=force_reindex)
    pagestore.save_pages(documents, source_file=pdf_path)

    print(f"Finished processing {pdf_path}")

def main():
    # Initialize components
    # text_splitter = TextSplitterComponent(chunk_size=1000, chunk_overlap=200)
    text_splitter = TextSplitterComponent(chunk_size=500, chunk_overlap=100)

    embeddings = EmbeddingsComponent()
    vectorstore = SQLiteVectorStore(db_file="vectors.db", table_name="vectors")
    vectorstore.embeddings_model = embeddings

    # Set up Cohere reranker (if COHERE_API_KEY is available)
    cohere_api_key = os.getenv("COHERE_API_KEY")
    if cohere_api_key:
        try:
            vectorstore.set_reranker(api_key=cohere_api_key)
            print("Cohere reranker initialized successfully!")
        except Exception as e:
            print(f"Failed to initialize Cohere reranker: {e}")
            print("Continuing without reranking capability.")
    else:
        print("COHERE_API_KEY not found in environment variables. Reranking will not be available.")

    pagestore = SQLitePageStore(db_file="pages.db", table_name="pages")

    # Check if database exists and offer to reset
    if os.path.exists("vectors.db"):
        reset = input("Existing database found. Would you like to reset it? (y/n): ")
        if reset.lower() == 'y':
            print("Resetting database...")
            vectorstore.drop_tables()
            print("Database reset complete.")

    while True:
        print("\nVector Store Menu:")
        print("1. Index new PDFs")
        print("2. View indexed sources")
        print("3. Search")
        print("4. Remove source")
        print("5. View statistics")
        print("6. Reset database")
        print("7. Ask question")
        print("8. Exit")
        
        choice = input("\nEnter your choice (1-8): ")
        
        if choice == "1":
            # Index new PDFs
            pdf_dir = "data"
            pdfs = list_pdfs(pdf_dir)
            
            if not pdfs:
                print(f"No PDF files found in {pdf_dir} directory!")
                continue
                
            print("\nAvailable PDFs:")
            for i, pdf in enumerate(pdfs, 1):
                print(f"{i}. {pdf}")
            
            selection = input("\nEnter PDF numbers to process (comma-separated) or 'all': ")
            force = input("Force reindex if already indexed? (y/n): ").lower() == 'y'
            
            if selection.lower() == 'all':
                selected_pdfs = pdfs
            else:
                try:
                    indices = [int(i) - 1 for i in selection.split(',')]
                    selected_pdfs = [pdfs[i] for i in indices]
                except:
                    print("Invalid selection!")
                    continue
            
            for pdf in selected_pdfs:
                pdf_path = os.path.join(pdf_dir, pdf)
                process_pdf(pdf_path, text_splitter, vectorstore, pagestore, force)
                
        elif choice == "2":
            # View indexed sources
            sources = vectorstore.get_indexed_sources()
            if not sources:
                print("No sources indexed yet!")
                continue
                
            print("\nIndexed Sources:")
            for i, source in enumerate(sources, 1):
                print(f"{i}. {source['source_file']}")
                print(f"   Indexed at: {source['indexed_at']}")
                print(f"   Documents: {source['document_count']}")
                
        elif choice == "3":
            # Search
            sources = vectorstore.get_indexed_sources()
            if not sources:
                print("No sources indexed yet!")
                continue
                
            print("\nAvailable sources:")
            for i, source in enumerate(sources, 1):
                print(f"{i}. {source['source_file']}")
            
            selection = input("\nEnter source numbers to search (comma-separated) or 'all': ")
            if selection.lower() == 'all':
                source_filter = None
            else:
                try:
                    indices = [int(i) - 1 for i in selection.split(',')]
                    source_filter = [sources[i]['source_file'] for i in indices]
                except:
                    print("Invalid selection!")
                    continue

            # Check if reranking is available
            use_reranker = False
            if hasattr(vectorstore, 'reranker') and vectorstore.reranker is not None:
                use_reranker = input("\nUse Cohere reranking for better results? (y/n): ").lower() == 'y'
            
            while True:
                query = input("\nEnter your search query (or 'back' to return to menu): ")
                if query.lower() == 'back':
                    break
                    
                k = int(input("Number of results to return (default: 3): ") or "3")
                
                if use_reranker:
                    rerank_top_k = int(input("Number of candidates to consider for reranking (default: 20): ") or "20")
                    results = vectorstore.similarity_search(
                        query=query, 
                        count=0, 
                        k=k, 
                        source_filter=source_filter,
                        rerank=True,
                        rerank_top_k=rerank_top_k
                    )
                    print(f"\nFound {len(results)} relevant documents (reranked with Cohere):")
                else:
                    results = vectorstore.similarity_search(
                        query=query, 
                        count=0, 
                        k=k, 
                        source_filter=source_filter
                    )
                    print(f"\nFound {len(results)} relevant documents:")
                
                for i, doc in enumerate(results, 1):
                    print(f"\nResult {i}:")
                    print(f"Source: {doc.metadata.get('source_file', 'Unknown')}")
                    print(f"Similarity: {doc.metadata.get('similarity_score', 'N/A')}")
                    if 'rerank_score' in doc.metadata:
                        print(f"Rerank score: {doc.metadata.get('rerank_score', 'N/A')}")
                    print("Content:", doc.page_content)
                    
        elif choice == "4":
            # Remove source
            sources = vectorstore.get_indexed_sources()
            if not sources:
                print("No sources indexed yet!")
                continue
                
            print("\nIndexed Sources:")
            for i, source in enumerate(sources, 1):
                print(f"{i}. {source['source_file']}")
                
            selection = input("\nEnter source number to remove: ")
            try:
                idx = int(selection) - 1
                source_to_remove = sources[idx]['source_file']
                confirm = input(f"Are you sure you want to remove {source_to_remove}? (y/n): ")
                if confirm.lower() == 'y':
                    vectorstore.remove_source(source_to_remove)
                    print(f"Removed {source_to_remove} from index")
                    confirm = input("Also remove {source_to_remove} from pages.db? (y/n): ")
                    if confirm.lower == 'y':
                        pagestore.remove_source(source_to_remove)

            except:
                print("Invalid selection!")
                
        elif choice == "5":
            # View statistics
            stats = vectorstore.get_collection_stats()
            
            print("\nCollection Statistics:")
            print("\nDocuments per source:")
            for source, count in stats['documents_per_source'].items():
                print(f"  {source}: {count} documents")
                
            print("\nSize per source:")
            for source, size in stats['size_per_source'].items():
                print(f"  {source}: {size/1024:.2f} KB")
                
            print("\nDate ranges:")
            for source, dates in stats['date_ranges'].items():
                print(f"  {source}:")
                print(f"    First document: {dates['first']}")
                print(f"    Last document: {dates['last']}")
                
            print(f"\nTotal documents: {stats['total_documents']}")

        elif choice == "6":
            # Reset database
            confirm = input("Are you sure you want to reset the database? This will delete all indexed documents! (y/n): ")
            if confirm.lower() == 'y':
                vectorstore.drop_tables()
                print("Database reset complete.")

        # added by Duc
        elif choice == "7":
            sources = vectorstore.get_indexed_sources()
            if not sources:
                print("No sources indexed yet!")
                continue
                
            print("\nAvailable sources:")
            for i, source in enumerate(sources, 1):
                print(f"{i}. {source['source_file']}")
            
            selection = input("\nEnter source numbers to search (comma-separated) or 'all': ")
            if selection.lower() == 'all':
                source_filter = None
            else:
                try:
                    indices = [int(i) - 1 for i in selection.split(',')]
                    source_filter = [sources[i]['source_file'] for i in indices]
                except:
                    print("Invalid selection!")
                    continue

            # Check if reranking is available for the question-answering function
            use_reranker = False
            if hasattr(vectorstore, 'reranker') and vectorstore.reranker is not None:
                use_reranker = input("\nUse Cohere reranking for better results? (y/n): ").lower() == 'y'
                if use_reranker:
                    rerank_top_k = int(input("Number of candidates to consider for reranking (default: 20): ") or "20")
            
            llm = GeminiService()
            crawler = IntelliresponseCrawler()

            while True:
                prompt = input("\nEnter your question (or 'back' to return to menu): ")
                if prompt.lower() == 'back':
                    break
                    
                k = int(input("Number of relevant text chunks to be consider each trial (default: 3): ") or "3")
                trials = int(input("Maximum number of trials (default: 5): ") or "5")

                # for i in range(trials):
                #     results = vectorstore.similarity_search(prompt, count=i, k=k, source_filter=source_filter)
                #     retrieved_docs = [doc.page_content for doc in results]

                #     llmResponse = llm.getResponse(prompt = prompt, relevant_context = "\n".join(retrieved_docs), type=2)
                #     print(llmResponse)
                #     found = int(llmResponse[0] or "1")
                #     print(found)
                #     if found:
                #         break

                # results = vectorstore.similarity_search(prompt, k=k, source_filter=source_filter)
                # print(f"\nFound {len(results)} relevant documents:")

                # for i, doc in enumerate(results, 1):
                #     print(f"\nResult {i}:")
                #     print(f"Source: {doc.metadata.get('source_file', 'Unknown')}")
                #     print(f"Similarity: {doc.metadata.get('similarity_score', 'N/A')}")
                #     print("Content:", doc.page_content[:200], "..." if len(doc.page_content) > 200 else "")
                #     print("Content:", doc.page_content)

                # retrieved_docs = [doc.page_content for doc in results]
                # retrieved_docs = [doc.metadata["full_page_content"] for doc in results]
                
                answered = False
                intelliresponseHint = crawler.getResponse(prompt)

                for trial in range(trials):
                    
                    # Use reranking if available and selected
                    if use_reranker:
                        results = vectorstore.similarity_search(
                            query=prompt, 
                            count=trial, 
                            k=k, 
                            source_filter=source_filter,
                            rerank=True,
                            rerank_top_k=rerank_top_k
                        )
                    else:
                        results = vectorstore.similarity_search(
                            prompt, 
                            count=trial, 
                            k=k, 
                            source_filter=source_filter
                        )
                    
                    retrieved_page_numbers = [int(doc.metadata["page_number"]) for doc in results]

                    retrieved_docs = []

                    for i in retrieved_page_numbers:
                        if (i > 1):
                             # also consider the previous page
                            retrieved_docs.append(pagestore.get_page_content(page_number=i-1, source_file=source_filter[0])) 

                        retrieved_docs.append(pagestore.get_page_content(page_number=i, source_file=source_filter[0]))  # source_filter[0] for now  

                        # < 1239 for now
                        if (i < 1239):
                            # also consider the next page
                            retrieved_docs.append(pagestore.get_page_content(page_number=i+1, source_file=source_filter[0]))    

                    llmResponse = llm.getResponse(prompt = prompt, relevant_context = "\n".join(retrieved_docs) + "\n" + intelliresponseHint)
                    
                    # if llm is able to answer
                    if not llmResponse[0] == "0" and not llmResponse[-1] == "0":
                        print("AI:", llmResponse)
                        answered = True
                        break
                    # else:
                    #     print(llmResponse)
                if not answered:
                    print("Could not find the information.")
                    print("AI:", llm.getResponseWithSearch(prompt=prompt))
            
        elif choice == "8":
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()

# main()