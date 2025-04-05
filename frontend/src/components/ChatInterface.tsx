// src/components/ChatInterface.tsx
"use client";

import { useState, useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import SourceDocument from "./SourceDocument";
import { Message } from "@/lib/types";

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  selectedFolder: string | null;
  isProcessing: boolean;
}

export default function ChatInterface({
  messages,
  onSendMessage,
  selectedFolder,
  isProcessing,
}: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [expandedSource, setExpandedSource] = useState<string | null>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputValue.trim() || !selectedFolder || isProcessing) return;

    onSendMessage(inputValue.trim());
    setInputValue("");

    // Focus the input after sending
    setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
  };

  // Handle input changes and auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);

    // Auto-resize the textarea
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Toggle source document expansion
  const toggleSource = (sourceId: string) => {
    if (expandedSource === sourceId) {
      setExpandedSource(null);
    } else {
      setExpandedSource(sourceId);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <svg
              className="w-12 h-12 mb-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
            <p className="text-base font-medium">Start a conversation</p>
            <p className="text-xs mt-1.5">
              Select a folder to begin querying your documents
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className="space-y-1.5">
              <MessageBubble message={message} />

              {/* Source documents section */}
              {message.sources && message.sources.length > 0 && (
                <div className="pl-4 mt-1">
                  <p className="text-[10px] text-gray-500 mb-1.5">Sources:</p>
                  <div className="space-y-1.5">
                    {message.sources.map((source, index) => (
                      <SourceDocument
                        key={`${message.id}-source-${index}`}
                        source={source}
                        isExpanded={
                          expandedSource === `${message.id}-source-${index}`
                        }
                        onToggle={() =>
                          toggleSource(`${message.id}-source-${index}`)
                        }
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t bg-white p-3">
        <form onSubmit={handleSubmit} className="flex space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={
                !selectedFolder
                  ? "Select a folder first..."
                  : isProcessing
                  ? "Processing documents..."
                  : "Ask a question about your documents..."
              }
              disabled={!selectedFolder || isProcessing}
              className="w-full border rounded-lg px-3 py-2 pr-12 resize-none min-h-[40px] max-h-[200px] focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-500 text-sm"
              rows={1}
            />
            <div className="absolute right-2 bottom-2 text-[10px] text-gray-400">
              {inputValue.length}/1000
            </div>
          </div>
          <button
            type="submit"
            disabled={!inputValue.trim() || !selectedFolder || isProcessing}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 flex items-center justify-center"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          </button>
        </form>
        <div className="flex items-center justify-between mt-1.5">
          <p className="text-[10px] text-gray-500">
            Press Enter to send, Shift+Enter for a new line
          </p>
          {isProcessing && (
            <div className="flex items-center text-xs text-yellow-600">
              <svg
                className="animate-spin -ml-1 mr-1.5 h-3 w-3"
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
              Processing...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
