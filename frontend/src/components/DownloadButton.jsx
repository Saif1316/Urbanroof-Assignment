import { useState } from "react";
import { downloadDDRPdf } from "../api/client";

export default function DownloadButton({ reportId }) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function handleDownload() {
    setIsDownloading(true);
    setErrorMessage("");
    try {
      const blob = await downloadDDRPdf(reportId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `DDR-Report-${reportId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setErrorMessage("Could not download the PDF. Try again.");
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <div className="download-button-wrap">
      <button
        className="download-button"
        onClick={handleDownload}
        disabled={isDownloading}
      >
        {isDownloading ? "Preparing PDF…" : "Download PDF"}
      </button>
      {errorMessage && <span className="download-error">{errorMessage}</span>}
    </div>
  );
}
