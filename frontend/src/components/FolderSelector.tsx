// src/components/FolderSelector.tsx
"use client";

import { useState } from "react";
import { useDriveFolder } from "@/hooks/useDriveFolder";

interface FolderSelectorProps {
  onFolderSelect: (folderId: string, folderName: string) => void;
  isProcessing: boolean;
  selectedFolder: string | null;
  folderName: string | null;
}

export default function FolderSelector({
  onFolderSelect,
  isProcessing,
  selectedFolder,
  folderName,
}: FolderSelectorProps) {
  const [isConnecting, setIsConnecting] = useState(false);
  const { connectToDrive, folders, isLoading, isConnected } = useDriveFolder();

  const handleConnectClick = async () => {
    setIsConnecting(true);
    try {
      await connectToDrive();
    } catch (error) {
      console.error("Failed to connect to Google Drive:", error);
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-gray-900">
          Google Drive Folders
        </h2>
        {isConnected && (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-green-100 text-green-800">
            Connected
          </span>
        )}
      </div>

      {!isConnected ? (
        <div className="flex flex-col items-center justify-center flex-1 p-4 text-center">
          <h3 className="text-base font-medium text-gray-900 mb-1.5">
            Connect to Google Drive
          </h3>
          <p className="text-xs text-gray-500 mb-4">
            Select a folder to start querying your documents
          </p>
          <button
            onClick={handleConnectClick}
            disabled={isConnecting}
            className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {isConnecting ? "Connecting..." : "Connect to Google Drive"}
          </button>
        </div>
      ) : (
        <div className="flex flex-col h-full">
          {selectedFolder ? (
            <div className="mb-4 p-3 border border-blue-200 rounded-lg bg-blue-50">
              <div className="flex items-center justify-between mb-1.5">
                <p className="font-medium text-blue-900 text-sm">
                  Selected Folder
                </p>
                <button
                  onClick={() => onFolderSelect("", "")}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Change
                </button>
              </div>
              <p className="text-xs text-blue-800 truncate">{folderName}</p>
            </div>
          ) : (
            <>
              <div className="mb-3">
                <p className="text-xs text-gray-600">
                  Select a folder to query documents from:
                </p>
              </div>

              {isLoading ? (
                <div className="flex flex-col items-center justify-center py-6">
                  <p className="text-xs text-gray-500">Loading folders...</p>
                </div>
              ) : folders.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-6 text-center">
                  <p className="text-xs text-gray-500">No folders found</p>
                </div>
              ) : (
                <div className="overflow-y-auto flex-1 -mx-2">
                  <ul className="space-y-1">
                    {folders.map((folder) => (
                      <li key={folder.id}>
                        <button
                          onClick={() => onFolderSelect(folder.id, folder.name)}
                          disabled={isProcessing}
                          className="w-full text-left px-2.5 py-1.5 rounded-md hover:bg-gray-100 transition-colors duration-200"
                        >
                          <span className="truncate text-xs text-gray-700 hover:text-gray-900">
                            {folder.name}
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          {isProcessing && (
            <div className="mt-3 p-3 border border-yellow-200 rounded-lg bg-yellow-50">
              <span className="text-xs text-yellow-800">
                Processing folder...
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
