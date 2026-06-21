import { useRef, useState } from "react";

export default function FileUpload({
  channelLabel,
  title,
  hint,
  accept,
  file,
  onFileSelected,
  onClear,
  disabled,
}) {
  const inputRef = useRef(null);
  const [isDragOver, setIsDragOver] = useState(false);

  function handleFiles(fileList) {
    const selected = fileList?.[0];
    if (!selected) return;
    if (accept && !selected.type.match(accept.replace("*", ".*"))) {
      return;
    }
    onFileSelected(selected);
  }

  function handleDrop(e) {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;
    handleFiles(e.dataTransfer.files);
  }

  return (
    <div className={`upload-card ${file ? "upload-card--filled" : ""}`}>
      <div className="upload-card-label">{channelLabel}</div>
      <h3 className="upload-card-title">{title}</h3>
      <p className="upload-card-hint">{hint}</p>

      {!file ? (
        <div
          className={`upload-dropzone ${isDragOver ? "upload-dropzone--drag" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            if (!disabled) setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => !disabled && inputRef.current?.click()}
          role="button"
          tabIndex={0}
          aria-disabled={disabled}
          onKeyDown={(e) => {
            if ((e.key === "Enter" || e.key === " ") && !disabled) {
              inputRef.current?.click();
            }
          }}
        >
          <span className="upload-dropzone-icon">↑</span>
          <span className="upload-dropzone-text">
            Drop PDF here or <span className="upload-dropzone-link">browse</span>
          </span>
          <input
            ref={inputRef}
            type="file"
            accept={accept}
            hidden
            disabled={disabled}
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>
      ) : (
        <div className="upload-preview">
          <div className="upload-preview-row">
            <span className="upload-preview-icon">PDF</span>
            <div className="upload-preview-meta">
              <span className="upload-preview-name">{file.name}</span>
              <span className="upload-preview-size">
                {(file.size / 1024).toFixed(0)} KB
              </span>
            </div>
          </div>
          <button
            type="button"
            className="upload-preview-clear"
            onClick={onClear}
            disabled={disabled}
          >
            Remove
          </button>
        </div>
      )}
    </div>
  );
}
