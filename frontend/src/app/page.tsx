// src/app/page.tsx
"use client";

import { useState } from "react";
import Header from "@/components/Header";
import FolderSelector from "@/components/FolderSelector";
import ChatInterface from "@/components/ChatInterface";
import { Message } from "@/lib/types";

export default function Home() {
  // State for the selected folder
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [folderName, setFolderName] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [chatHistory, setChatHistory] = useState<Message[]>([
    {
      id: "0",
      role: "system",
      content:
        "Hello! Select a Google Drive folder to start querying your documents.",
    },
  ]);

  // Handle folder selection
  const handleFolderSelect = async (folderId: string, name: string) => {
    setIsProcessing(true);
    setSelectedFolder(folderId);
    setFolderName(name);

    try {
      // Call API to process the folder
      const response = await fetch("/api/process-folder", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ folder_id: folderId }),
      });

      const data = await response.json();

      if (response.ok) {
        // Add a system message indicating the folder was processed
        setChatHistory((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: "system",
            content: `Folder "${name}" has been processed. You can now ask questions about your documents.`,
          },
        ]);
      } else {
        setChatHistory((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: "system",
            content: `Error processing folder: ${
              data.detail || "Unknown error"
            }`,
          },
        ]);
        setSelectedFolder(null);
        setFolderName(null);
      }
    } catch (error) {
      console.error("Error processing folder:", error);
      setChatHistory((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "system",
          content: "Error processing folder. Please try again.",
        },
      ]);
      setSelectedFolder(null);
      setFolderName(null);
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle sending a message
  const handleSendMessage = async (message: string) => {
    if (!selectedFolder) return;

    // Add user message to chat
    const userMessageId = Date.now().toString();
    setChatHistory((prev) => [
      ...prev,
      {
        id: userMessageId,
        role: "user",
        content: message,
      },
    ]);

    // Add temporary assistant message
    const assistantMessageId = (Date.now() + 1).toString();
    setChatHistory((prev) => [
      ...prev,
      {
        id: assistantMessageId,
        role: "assistant",
        content: "...",
        isLoading: true,
      },
    ]);

    try {
      // Call API to query
      const response = await fetch("/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: message,
          folder_id: selectedFolder,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        // Update assistant message with response
        setChatHistory((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content: data.answer,
                  sources: data.sources,
                  isLoading: false,
                }
              : msg
          )
        );
      } else {
        // Update with error message
        setChatHistory((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content: `Error: ${data.detail || "Failed to get response"}`,
                  isLoading: false,
                }
              : msg
          )
        );
      }
    } catch (error) {
      console.error("Error querying:", error);
      // Update with error message
      setChatHistory((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: "Error processing your query. Please try again.",
                isLoading: false,
              }
            : msg
        )
      );
    }
  };

  return (
    <div className="flex flex-col h-screen">
      <Header />

      <main className="flex flex-col flex-1 p-4 overflow-hidden">
        <div className="flex flex-col md:flex-row gap-4 h-full">
          {/* Sidebar with folder selector */}
          <div className="w-full md:w-64 bg-white rounded-lg shadow p-4">
            <FolderSelector
              onFolderSelect={handleFolderSelect}
              isProcessing={isProcessing}
              selectedFolder={selectedFolder}
              folderName={folderName}
            />
          </div>

          {/* Main chat interface */}
          <div className="flex-1 bg-white rounded-lg shadow overflow-hidden flex flex-col">
            <ChatInterface
              messages={chatHistory}
              onSendMessage={handleSendMessage}
              selectedFolder={selectedFolder}
              isProcessing={isProcessing}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
