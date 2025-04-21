// FolderMetaManager manages folder metadata, id-folder map, processed state, and provides structure retrieval

export interface Folder {
    id: string;
    name: string;
    children: Folder[];
    processed: boolean;  // Placeholder for processed status
    // lastProcessed: string; // last processed date. We should load indexes from db first
}

export class FolderMetaManager {
  private folders: Folder[] = [];
  private folderMap: Map<string, Folder> = new Map();

  constructor(folders: Folder[] = []) {
    this.setFolders(folders);
  }

  /**
   * Set folders and build the folder map.
   * @param folders 
   */
  setFolders(folders: Folder[]) {
    this.folders = folders;
    this.folderMap.clear();
    this._buildMap(folders);
  }

  private _buildMap(folders: Folder[]) {
    for (const folder of folders) {
      this.folderMap.set(folder.id, folder);
      if (folder.children && folder.children.length > 0) {
        this._buildMap(folder.children);
      }
    }
  }

  getFolderById(id: string): Folder | undefined {
    return this.folderMap.get(id);
  }

  updateProcessedState(id: string, processed: boolean) {
    const folder = this.folderMap.get(id);
    if (folder) {
      folder.processed = processed;
    }
  }

  getFolderStructure(): Folder[] {
    return this.folders;
  }
}
