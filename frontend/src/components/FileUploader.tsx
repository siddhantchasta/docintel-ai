'use client';

import { useState, useRef, useCallback, type DragEvent, type ChangeEvent } from 'react';

interface FileUploaderProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
}

const ACCEPTED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif'];
const ACCEPTED_MIME_TYPES = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'image/tiff',
];

function isAcceptedFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return (
    ACCEPTED_MIME_TYPES.includes(file.type) ||
    ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext))
  );
}

export default function FileUploader({ onFilesSelected, disabled }: FileUploaderProps) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (fileList: FileList | null) => {
      if (!fileList || disabled) return;
      const accepted = Array.from(fileList).filter(isAcceptedFile);
      if (accepted.length > 0) {
        onFilesSelected(accepted);
      }
      // Reset input so re-selecting same file works
      if (inputRef.current) {
        inputRef.current.value = '';
      }
    },
    [onFilesSelected, disabled],
  );

  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setDragActive(true);
  }

  function handleDragLeave(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleFiles(e.dataTransfer.files);
  }

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    handleFiles(e.target.files);
  }

  return (
    <div
      className={`dropzone ${dragActive ? 'drag-active' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS.join(',')}
        multiple
        onChange={handleChange}
        style={{ display: 'none' }}
      />

      <div className="dropzone-icon">
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
      </div>

      <h3>
        {dragActive ? 'Drop files to upload' : 'Drag & drop files here'}
      </h3>
      <p>or click to select files from your computer</p>
      <div className="dropzone-accept">
        Supported file types: PDF, PNG, JPEG, TIFF
      </div>
    </div>
  );
}
