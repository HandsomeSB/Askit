// src/components/SourceDocument.tsx
import { formatMimeType, truncateText } from "@/utils/formatters";
import { Source } from "@/lib/types";

interface SourceDocumentProps {
  source: Source;
  isExpanded: boolean;
  onToggle: () => void;
}

export default function SourceDocument({
  source,
  isExpanded,
  onToggle,
}: SourceDocumentProps) {
  const { file_name, file_id, mime_type, text, score } = source;

  // Get file type icon based on mime type
  const getFileIcon = () => {
    if (mime_type.includes("pdf")) {
      return (
        <svg
          className="w-5 h-5 text-red-500"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
        </svg>
      );
    } else if (mime_type.includes("word")) {
      return (
        <svg
          className="w-5 h-5 text-blue-500"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
        </svg>
      );
    } else if (
      mime_type.includes("spreadsheet") ||
      mime_type.includes("excel")
    ) {
      return (
        <svg
          className="w-5 h-5 text-green-500"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
        </svg>
      );
    } else if (mime_type.includes("image")) {
      return (
        <svg
          className="w-5 h-5 text-purple-500"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
            clipRule="evenodd"
          />
        </svg>
      );
    } else {
      return (
        <svg
          className="w-5 h-5 text-gray-500"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm4 10a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
            clipRule="evenodd"
          />
        </svg>
      );
    }
  };

  // Format relevance score as percentage
  const relevancePercentage = Math.round(score * 100);

  return (
    <div className="border rounded-md overflow-hidden bg-white">
      <div
        className="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-gray-50"
        onClick={onToggle}
      >
        <div className="flex items-center space-x-2">
          {getFileIcon()}
          <span className="text-sm font-medium truncate max-w-[200px]">
            {file_name}
          </span>
          <span className="text-xs text-gray-500">
            ({formatMimeType(mime_type)})
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
            {relevancePercentage}% relevant
          </span>
          <button className="text-gray-500 hover:text-gray-700">
            <svg
              className={`w-5 h-5 transition-transform ${
                isExpanded ? "transform rotate-180" : ""
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="px-3 py-2 border-t text-sm text-gray-700 whitespace-pre-wrap bg-gray-50">
          {text}
        </div>
      )}
    </div>
  );
}
