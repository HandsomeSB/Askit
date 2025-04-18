from dotenv import load_dotenv
load_dotenv()

from indexer import embed_folder

index = embed_folder("data")
retriever = index.as_retriever(similarity_top_k=5)
print("Query engine built")
response = retriever.retrieve("Oil and gas industry")

for src in response:
    print("File:", src.node.metadata["source"])
    print("Excerpt:", src.text)
    print("Score:", src.score) 
    print("---")