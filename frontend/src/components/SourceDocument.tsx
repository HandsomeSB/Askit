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

  // Format relevance score as percentage
  const relevancePercentage = Math.round(score * 100);

  return (
    <div className="border rounded-md overflow-hidden bg-white">
      <div
        className="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-gray-50"
        onClick={onToggle}
      >
        <div className="flex items-center space-x-2">
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
            {isExpanded ? "▼" : "▲"}
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
