from llama_index.core import Document

def get_file_paths(directory):
    import os
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".txt"):
                file_paths.append(os.path.join(root, file))
    return file_paths

def get_docs(file_paths):
    docs = []
    for path in file_paths:
        text = open(path, "r").read()
        meta = {
            "source": path,
            "title": path.split("/")[-1],
            "author": "Your Name",
            # add any other fields here
        }
        docs.append(Document(text=text, metadata=meta))
    print("docs prepared")
    return docs