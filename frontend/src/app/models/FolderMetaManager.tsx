// FolderMetaManager manages folder metadata, id-folder map, processed state, and provides structure retrieval
import SearchService from "../../services/SearchService";
import { FolderStructureResponse, IndexMetaResponse } from "@/types/types";

// NOTE, Moving the processed logic back to the server side
export interface Folder {
  id: string;
  name: string;
  children?: Folder[];
  modifiedTime: string;
  contentModifiedTime: string;
  processed: boolean; 
}

export class FolderMetaManager {
  private folders: Folder[] = [];
  private folderMap: Map<string, Folder> = new Map();
  private folderMetaMap: Map<string, IndexMetaResponse> = new Map();
  private searchService: SearchService = new SearchService();

  constructor(folders: Folder[] = []) {
    this.setFolders(folders);
  }

  /**
   * Fetch folder structure and metadata from the server.
   * This function will set the folders and their processed state.
   */
  async fetchFolderMeta() {
    const [folderStruct, folderMeta] = await Promise.all([
      this.searchService.getFolderStructure(),
      this.searchService.getIndexMeta()
    ]);

    // Helper function to type cast
    const transferData = (folderStructObj : FolderStructureResponse): Folder => {
      return {
        id: folderStructObj.id,
        name: folderStructObj.name,
        processed: false,
        modifiedTime: folderStructObj.modifiedTime,
        contentModifiedTime: folderStructObj.contentModifiedTime,
        children: folderStructObj.children
          ? folderStructObj.children.map(transferData)
          : [],
      }
    }
    const folders = folderStruct.map(transferData);
    this.setFolders(folders);
    this._buildMetaMap(folderMeta);
    this._updateProcessedStateAll();

    console.log(this.folderMap);
    console.log(this.folderMetaMap);
  }

  /**
   * Fetch folder metadata from the server and update processed states. 
   * Use after folder is processed. 
   */
  async refreshFolderMeta() {
    const folderMeta = await this.searchService.getIndexMeta();
    this._buildMetaMap(folderMeta);
    this._updateProcessedStateAll();
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

  private _buildMetaMap = (folderMetas: IndexMetaResponse[]): void => {
    for (const meta of folderMetas) {
      this.folderMetaMap.set(meta.folder_id, meta);
      this._buildMetaMap(meta.children || []);
    }
  }

  private _updateProcessedStateAll = (): void => {
    for(const [key, value] of this.folderMap) {
      const meta = this.folderMetaMap.get(key);
      const folder = this.folderMap.get(key);

      const contentModifiedTime = new Date(folder?.contentModifiedTime || "");
      const indexedTime = new Date(meta?.time_indexed || "");


      value.processed = (indexedTime >= contentModifiedTime);
      this.folderMap.set(key, value);
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
