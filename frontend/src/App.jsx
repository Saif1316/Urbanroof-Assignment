import { useState } from "react";
import FileUpload from "./components/FileUpload";
import PipelineStatus from "./components/PipelineStatus";
import DDRReportView from "./components/DDRReportView";
import { generateDDR } from "./api/client";
import "./styles/app.css";

// Pipeline stages, in order. Drives the PipelineStatus visualization.
const STAGES = ["idle", "extracting", "analyzing", "merging", "ready", "error"];

export default function App() {
  const [inspectionFile, setInspectionFile] = useState(null);
  const [thermalFile, setThermalFile] = useState(null);
  const [stage, setStage] = useState("idle");
  const [report, setReport] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  const bothUploaded = inspectionFile && thermalFile;

  async function handleGenerate() {
    setStage("extracting");
    setErrorMessage("");
    try {
      // Simulated stage progression for user feedback while the single
      // backend call runs — the backend does extracting/analyzing/merging
      // in one request, but showing intermediate stages keeps the user
      // oriented on what's happening.
      const stageTimer = setTimeout(() => setStage("analyzing"), 900);
      const stageTimer2 = setTimeout(() => setStage("merging"), 1800);

      const result = await generateDDR(inspectionFile, thermalFile);

      clearTimeout(stageTimer);
      clearTimeout(stageTimer2);
      setReport(result);
      setStage("ready");
    } catch (err) {
      setErrorMessage(
        err?.message || "Something went wrong while generating the report."
      );
      setStage("error");
    }
  }

  function handleReset() {
    setInspectionFile(null);
    setThermalFile(null);
    setReport(null);
    setErrorMessage("");
    setStage("idle");
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-eyebrow">DDR Generation System</span>
        <h1 className="app-title">Detailed Diagnostic Report Builder</h1>
        <p className="app-subtitle">
          Upload an inspection report and a thermal report. The system reads
          both, merges overlapping findings, and produces one structured,
          client-ready DDR.
        </p>
      </header>

      <PipelineStatus stage={stage} />

      {stage !== "ready" && (
        <main className="upload-grid">
          <FileUpload
            channelLabel="Channel 1"
            title="Inspection Report"
            hint="Site observations, issue descriptions, photos"
            accept="application/pdf"
            file={inspectionFile}
            onFileSelected={setInspectionFile}
            onClear={() => setInspectionFile(null)}
            disabled={stage === "extracting" || stage === "analyzing" || stage === "merging"}
          />

          <div className="upload-connector" aria-hidden="true">
            <span className="connector-plus">+</span>
          </div>

          <FileUpload
            channelLabel="Channel 2"
            title="Thermal Report"
            hint="Temperature readings, thermal imaging findings"
            accept="application/pdf"
            file={thermalFile}
            onFileSelected={setThermalFile}
            onClear={() => setThermalFile(null)}
            disabled={stage === "extracting" || stage === "analyzing" || stage === "merging"}
          />
        </main>
      )}

      {stage === "error" && (
        <div className="error-banner" role="alert">
          <strong>Generation failed.</strong> {errorMessage}
        </div>
      )}

      {stage !== "ready" && (
        <div className="generate-row">
          <button
            className="generate-button"
            disabled={!bothUploaded || stage === "extracting" || stage === "analyzing" || stage === "merging"}
            onClick={handleGenerate}
          >
            {stage === "extracting" || stage === "analyzing" || stage === "merging"
              ? "Generating…"
              : "Generate DDR"}
          </button>
          {!bothUploaded && (
            <span className="generate-hint">Upload both documents to continue</span>
          )}
        </div>
      )}

      {stage === "ready" && report && (
        <DDRReportView report={report} onStartOver={handleReset} />
      )}
    </div>
  );
}
