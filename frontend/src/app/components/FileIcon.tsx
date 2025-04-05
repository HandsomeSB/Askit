'use client';

import React from 'react';

interface FileIconProps {
  mimeType: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export default function FileIcon({ mimeType, size = 'md', className = '' }: FileIconProps) {
  // Determine icon based on mimeType
  let icon = '📄'; // Default document
  
  // Images
  if (mimeType.includes('image/')) {
    icon = '🖼️';
  }
  // Google Docs
  else if (mimeType.includes('application/vnd.google-apps.document')) {
    icon = '📝';
  }
  // Google Sheets
  else if (mimeType.includes('application/vnd.google-apps.spreadsheet') || 
           mimeType.includes('spreadsheet') ||
           mimeType.includes('excel')) {
    icon = '📊';
  }
  // Google Slides
  else if (mimeType.includes('application/vnd.google-apps.presentation') || 
           mimeType.includes('presentation') ||
           mimeType.includes('powerpoint')) {
    icon = '📑';
  }
  // PDF
  else if (mimeType.includes('application/pdf')) {
    icon = '📕';
  }
  // Folder
  else if (mimeType.includes('folder')) {
    icon = '📁';
  }
  // Audio
  else if (mimeType.includes('audio/')) {
    icon = '🎵';
  }
  // Video
  else if (mimeType.includes('video/')) {
    icon = '🎬';
  }
  // Archive
  else if (mimeType.includes('zip') || 
           mimeType.includes('tar') || 
           mimeType.includes('rar') || 
           mimeType.includes('archive')) {
    icon = '🗃️';
  }
  // Code
  else if (mimeType.includes('application/json') || 
           mimeType.includes('text/html') || 
           mimeType.includes('text/css') || 
           mimeType.includes('javascript')) {
    icon = '💻';
  }
  
  // Size classes
  const sizeClass = {
    sm: 'text-2xl',
    md: 'text-3xl',
    lg: 'text-4xl',
  }[size];
  
  return (
    <span className={`flex-shrink-0 ${sizeClass} ${className}`}>
      {icon}
    </span>
  );
}