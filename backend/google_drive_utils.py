from document_processor import DocumentProcessor
from fastapi import HTTPException



def get_absolute_path(drive_service, folder_id):
    """
    Get the absolute path of a folder in Google Drive.
    
    Parameters:
    - drive_service: Authenticated Google Drive service instance.
    - folder_id: ID of the folder to get the absolute path for.
    
    Returns:
    - A string representing the absolute path of the folder.
    """
    path = []
    current_folder_id = folder_id

    while current_folder_id:
        # Get folder metadata
        folder_metadata = drive_service.files().get(
            fileId=current_folder_id,
            fields="id, name, parents"
        ).execute()

        # Add the folder name to the path
        path.append(folder_metadata["name"])

        # Move to the parent folder (if it exists)
        parents = folder_metadata.get("parents")
        current_folder_id = parents[0] if parents else None

    # Reverse the path to get the absolute path from root to the folder
    return "/" + "/".join(reversed(path))

def get_absolute_path_id(drive_service, folder_id):
    """
    Get the absolute path of a folder in Google Drive.
    
    Parameters:
    - drive_service: Authenticated Google Drive service instance.
    - folder_id: ID of the folder to get the absolute path for.
    
    Returns:
    - A string representing the absolute path of the folder, with all the folder ids.
    """
    path = []
    current_folder_id = folder_id

    while current_folder_id:
        # Get folder metadata
        folder_metadata = drive_service.files().get(
            fileId=current_folder_id,
            fields="id, name, parents"
        ).execute()

        # Add the folder name to the path
        path.append(folder_metadata["id"])

        # Move to the parent folder (if it exists)
        parents = folder_metadata.get("parents")
        current_folder_id = parents[0] if parents else None

    # Reverse the path to get the absolute path from root to the folder
    return "/" + "/".join(reversed(path))

def index_folder(drive_service, document_indexer, folder_id, absolute_id_path=None):
    """
    Index a folder recursively in Google Drive.
    
    This function retrieves all files in a specified folder and indexes them.
    """
    user_document_processor = DocumentProcessor(drive_service=drive_service)
    # Get all files from the folder
    try:
        files = user_document_processor.get_files_from_drive(folder_id)
        if not files:
            raise HTTPException(
                status_code=400,
                detail="No files found in the specified folder"
            )
    except Exception as drive_error:
        print(f"Error accessing Google Drive: {str(drive_error)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to access Google Drive: {str(drive_error)}",
        )
    
    # Process each file and convert to documents
    documents = []
    failed_files = []
    subfolders = []
    for file in files:
        # Skip folders, append to subfolders list
        if file.get("mimeType") == "application/vnd.google-apps.folder":
            subfolders.append(file)
            continue
        try:
            file_documents = user_document_processor.process_file(file)
            if file_documents:
                documents.extend(file_documents)
            else:
                failed_files.append(f"{file.get('name', 'unknown')} (no content extracted)")
        except Exception as file_error:
            print(f"Error processing file {file.get('name', 'unknown')}: {str(file_error)}")
            import traceback
            print(traceback.format_exc())
            failed_files.append(f"{file.get('name', 'unknown')} ({str(file_error)})")
            continue
    
    if not documents:
        error_message = "No documents were successfully processed from the folder."
        if failed_files:
            error_message += f" Failed files: {', '.join(failed_files)}"
        raise HTTPException(
            status_code=500,
            detail=error_message
        )
    
    # Create index from documents
    try:
        if not absolute_id_path:
            absolute_id_path = get_absolute_path_id(drive_service, folder_id)
        
        index_id = document_indexer.create_index(documents, folder_id, absolute_id_path)
    except Exception as index_error:
        print(f"Error creating index: {str(index_error)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create index: {str(index_error)}"
        )
    
    # Keep track of the number of files processed
    total_files = len(files)
    
    # Process subfolders recursively
    for subfolder in subfolders:
        try:
            subfolder_id = subfolder.get("id")
            subfolder_name = subfolder.get("name")
            print(f"Processing subfolder: {subfolder_name} (ID: {subfolder_id})")
            res, len_files = index_folder(drive_service, document_indexer, subfolder_id, f"{absolute_id_path}/{subfolder_id}") 
            total_files += len_files
        except Exception as subfolder_error:
            print(f"Error processing subfolder {subfolder.get('name', 'unknown')}: {str(subfolder_error)}")
            import traceback
            print(traceback.format_exc())
            failed_files.append(f"{subfolder.get('name', 'unknown')} ({str(subfolder_error)})")
            continue

    response = {
        "status": "success",
        "message": f"Processed {total_files} items",
        "index_id": "bro I have no clue what this is", # NOTE, fix
    }
    
    if failed_files:
        response["failed_files"] = failed_files
        
    return response, total_files