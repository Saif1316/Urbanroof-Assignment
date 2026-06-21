import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // generation can be slow with ML model inference
});

/**
 * Sends both PDFs to the backend and returns the structured DDR JSON.
 * @param {File} inspectionFile
 * @param {File} thermalFile
 * @returns {Promise<object>} DDR report object matching the 7-section schema
 */
export async function generateDDR(inspectionFile, thermalFile) {
  const formData = new FormData();
  formData.append("inspection_report", inspectionFile);
  formData.append("thermal_report", thermalFile);

  const response = await apiClient.post("/api/generate-ddr", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
}

/**
 * Downloads the generated DDR as a PDF blob.
 * @param {string} reportId
 * @returns {Promise<Blob>}
 */
export async function downloadDDRPdf(reportId) {
  const response = await apiClient.get(`/api/download-pdf/${reportId}`, {
    responseType: "blob",
  });
  return response.data;
}
