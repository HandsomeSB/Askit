import os
from dotenv import load_dotenv
from indexer import DocumentIndexer
from query_engine import EnhancedQueryEngine

# Load environment variables
load_dotenv()

def main():
    """
    Example usage of the Google Drive indexer and query engine.
    
    This demonstrates how to:
    1. Connect to Google Drive
    2. Process files from a specific folder
    3. Index the documents
    4. Query the index
    """
    # Replace with your Google Drive folder ID
    folder_id = "YOUR_GOOGLE_DRIVE_FOLDER_ID"
    
    print(f"Starting document processing for folder: {folder_id}")
    
    # Initialize the document indexer
    indexer = DocumentIndexer()
    
    # Process and index the Google Drive folder
    index_id = indexer.process_and_index_drive_folder(folder_id)
    print(f"Created index with ID: {index_id}")
    
    # Initialize the query engine
    query_engine = EnhancedQueryEngine(top_k=5)
    
    # Example queries
    example_queries = [
        "What are the main points in the documents?",
        "Find documents from last month",
        "Show me all PDF documents",
        "Find content related to machine learning",
    ]
    
    # Perform queries
    for query in example_queries:
        print(f"\nQuery: {query}")
        answer, sources = query_engine.query(query, folder_id)
        
        print(f"Answer: {answer}")
        print(f"Found {len(sources)} sources:")
        
        # Display source information
        for i, source in enumerate(sources):
            print(f"  Source {i+1}: {source['file_name']} (Score: {source['score']})")
            if 'metadata' in source and 'web_view_link' in source['metadata']:
                print(f"    Link: {source['metadata']['web_view_link']}")
    
    print("\nExample completed successfully!")

if __name__ == "__main__":
    main()
