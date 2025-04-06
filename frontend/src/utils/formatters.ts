// src/utils/formatters.ts

/**
 * Format a MIME type to a more readable format
 * @param mimeType The MIME type to format
 * @returns A formatted string representation of the MIME type
 */
export function formatMimeType(mimeType: string): string {
  if (!mimeType) {
    return "Unknown";
  }

  if (mimeType.includes("pdf")) {
    return "PDF";
  } else if (mimeType.includes("word")) {
    return "Word";
  } else if (mimeType.includes("spreadsheet") || mimeType.includes("excel")) {
    return "Excel";
  } else if (
    mimeType.includes("presentation") ||
    mimeType.includes("powerpoint")
  ) {
    return "PowerPoint";
  } else if (mimeType.includes("image")) {
    return "Image";
  } else if (mimeType.includes("audio")) {
    return "Audio";
  } else if (mimeType.includes("video")) {
    return "Video";
  } else if (mimeType.includes("text/plain")) {
    return "Text";
  } else if (mimeType.includes("text/html") || mimeType.includes("htm")) {
    return "HTML";
  } else {
    // Extract the subtype from the MIME type (e.g., "pdf" from "application/pdf")
    const parts = mimeType.split("/");
    if (parts.length > 1) {
      return parts[1].charAt(0).toUpperCase() + parts[1].slice(1);
    }
    return "Unknown";
  }
}

/**
 * Truncate text to a specific length with ellipsis
 * @param text The text to truncate
 * @param maxLength Maximum length of the result
 * @returns The truncated text
 */
export function truncateText(text: string, maxLength: number = 100): string {
  if (text.length <= maxLength) {
    return text;
  }

  return text.substring(0, maxLength - 3) + "...";
}

/**
 * Format a file size in bytes to a human-readable string
 * @param bytes File size in bytes
 * @returns Human-readable file size (e.g., "1.5 MB")
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

/**
 * Format a date string or timestamp to a human-readable format
 * @param date Date string or timestamp
 * @returns Formatted date string
 */
export function formatDate(date: string | number): string {
  const dateObj = new Date(date);
  return dateObj.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/**
 * Calculate time elapsed since a given date/time
 * @param date Date string or timestamp
 * @returns Human-readable time elapsed (e.g., "5 minutes ago")
 */
export function timeAgo(date: string | number): string {
  const dateObj = new Date(date);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000);

  let interval = Math.floor(seconds / 31536000);
  if (interval >= 1) {
    return interval === 1 ? "1 year ago" : `${interval} years ago`;
  }

  interval = Math.floor(seconds / 2592000);
  if (interval >= 1) {
    return interval === 1 ? "1 month ago" : `${interval} months ago`;
  }

  interval = Math.floor(seconds / 86400);
  if (interval >= 1) {
    return interval === 1 ? "1 day ago" : `${interval} days ago`;
  }

  interval = Math.floor(seconds / 3600);
  if (interval >= 1) {
    return interval === 1 ? "1 hour ago" : `${interval} hours ago`;
  }

  interval = Math.floor(seconds / 60);
  if (interval >= 1) {
    return interval === 1 ? "1 minute ago" : `${interval} minutes ago`;
  }

  return seconds < 10 ? "just now" : `${Math.floor(seconds)} seconds ago`;
}
