// src/hooks/useDriveFolder.ts
import { useState, useEffect, useCallback } from "react";
import { Folder } from "@/lib/types";

export function useDriveFolder() {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Function to connect to Google Drive
  const connectToDrive = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Call the backend API to authenticate with Google Drive
      const response = await fetch("/api/auth/google-drive", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to authenticate with Google Drive");
      }

      // After successful authentication, fetch the folders
      const foldersResponse = await fetch("/api/folders", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!foldersResponse.ok) {
        throw new Error("Failed to fetch folders from Google Drive");
      }

      const foldersData = await foldersResponse.json();
      setFolders(foldersData);
      setIsConnected(true);

      return true;
    } catch (err) {
      setError("Failed to connect to Google Drive. Please try again.");
      console.error("Error connecting to Google Drive:", err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    folders,
    isLoading,
    isConnected,
    error,
    connectToDrive,
  };
}
