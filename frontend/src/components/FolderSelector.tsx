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
          <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center mb-3">
            <svg
              className="w-6 h-6 text-blue-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>
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
            {isConnecting ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-1.5 h-3 w-3 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Connecting...
              </>
            ) : (
              "Connect to Google Drive"
            )}
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
                  className="text-xs text-blue-600 hover:text-blue-800 flex items-center"
                >
                  <svg
                    className="w-3 h-3 mr-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 19l-7-7 7-7"
                    />
                  </svg>
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
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mb-1.5"></div>
                  <p className="text-xs text-gray-500">Loading folders...</p>
                </div>
              ) : folders.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-6 text-center">
                  <svg
                    className="w-8 h-8 text-gray-400 mb-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                    />
                  </svg>
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
                          className="w-full text-left px-2.5 py-1.5 rounded-md hover:bg-gray-100 flex items-center group transition-colors duration-200"
                        >
                          <svg
                            className="w-4 h-4 mr-2 text-yellow-500 group-hover:text-yellow-600"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M2 6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"
                              clipRule="evenodd"
                            />
                          </svg>
                          <span className="truncate text-xs text-gray-700 group-hover:text-gray-900">
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
            <div className="mt-3 p-3 border border-yellow-200 rounded-lg bg-yellow-50 flex items-center">
              <svg
                className="animate-spin -ml-1 mr-1.5 h-3 w-3 text-yellow-600"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
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
