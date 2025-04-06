// src/components/Header.tsx
import React from "react";
import Image from "next/image";

const Header: React.FC = () => {
  return (
    <header className="w-full bg-white shadow-sm border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                RAG Application
              </h1>
              <p className="text-xs text-gray-500">Document Retrieval System</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <a
              href="https://github.com/yourusername/rag-app"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-500 hover:text-gray-700"
            >
              GitHub
            </a>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
