// src/components/MessageBubble.tsx
import { Message } from "@/lib/types";

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const { role, content, isLoading } = message;

  // Determine styles based on message role
  const getBubbleStyles = () => {
    switch (role) {
      case "user":
        return "bg-blue-500 text-white ml-auto";
      case "assistant":
        return "bg-gray-100 text-gray-800";
      case "system":
        return "bg-yellow-50 text-gray-700 border border-yellow-200 mx-auto";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  // Format content with line breaks and code blocks
  const formatContent = (text: string) => {
    const parts = text.split(/(```[\s\S]*?```)/g);
    return parts.map((part, i) => {
      if (part.startsWith("```")) {
        const code = part.slice(3, -3).trim();
        return (
          <pre
            key={i}
            className="bg-gray-800 text-white p-2 rounded-lg overflow-x-auto my-1 text-sm"
          >
            <code>{code}</code>
          </pre>
        );
      }
      return part.split("\n").map((line, j) => (
        <span key={`${i}-${j}`}>
          {line}
          {j < part.split("\n").length - 1 && <br />}
        </span>
      ));
    });
  };

  return (
    <div
      className={`flex items-start space-x-2 max-w-3xl ${
        role === "user" ? "ml-auto" : "mr-auto"
      }`}
    >
      <div
        className={`flex flex-col ${
          role === "user" ? "items-end" : "items-start"
        }`}
      >
        <div className={`rounded-lg px-3 py-1.5 text-sm ${getBubbleStyles()}`}>
          {isLoading ? (
            <div className="flex items-center space-x-1.5">
              <div
                className="w-1.5 h-1.5 bg-current rounded-full animate-bounce"
                style={{ animationDelay: "0ms" }}
              ></div>
              <div
                className="w-1.5 h-1.5 bg-current rounded-full animate-bounce"
                style={{ animationDelay: "150ms" }}
              ></div>
              <div
                className="w-1.5 h-1.5 bg-current rounded-full animate-bounce"
                style={{ animationDelay: "300ms" }}
              ></div>
            </div>
          ) : (
            <div className="whitespace-pre-wrap break-words prose prose-sm max-w-none">
              {formatContent(content)}
            </div>
          )}
        </div>
        <span className="text-[10px] text-gray-500 mt-0.5">
          {role === "user"
            ? "You"
            : role === "assistant"
            ? "Assistant"
            : "System"}
        </span>
      </div>
    </div>
  );
}
