import AreaObservationCard from "./AreaObservationCard";
import DownloadButton from "./DownloadButton";

export default function DDRReportView({ report, onStartOver }) {
  const {
    report_id,
    property_issue_summary,
    area_observations,
    overall_severity,
    overall_severity_reasoning,
    recommended_actions,
    additional_notes,
    missing_or_unclear_information,
  } = report;

  return (
    <div className="report-view">
      <div className="report-toolbar">
        <span className="report-id">Report ID: {report_id || "Not Available"}</span>
        <div className="report-toolbar-actions">
          <DownloadButton reportId={report_id} />
          <button className="start-over-button" onClick={onStartOver}>
            Start New Report
          </button>
        </div>
      </div>

      <section className="report-section">
        <h2 className="report-section-title">01 — Property Issue Summary</h2>
        <p className="report-section-text">
          {property_issue_summary || "Not Available"}
        </p>
      </section>

      <section className="report-section">
        <h2 className="report-section-title">02 — Area-wise Observations</h2>
        <div className="area-card-list">
          {area_observations && area_observations.length > 0 ? (
            area_observations.map((area, idx) => (
              <AreaObservationCard area={area} key={area.area_name || idx} />
            ))
          ) : (
            <p className="report-section-text">Not Available</p>
          )}
        </div>
      </section>

      <section className="report-section">
        <h2 className="report-section-title">03 — Severity Assessment</h2>
        <p className="report-section-text">
          <strong>Overall Severity:</strong> {overall_severity || "Not Available"}
        </p>
        <p className="report-section-text">{overall_severity_reasoning || "Not Available"}</p>
      </section>

      <section className="report-section">
        <h2 className="report-section-title">04 — Recommended Actions</h2>
        {recommended_actions && recommended_actions.length > 0 ? (
          <ul className="report-list">
            {recommended_actions.map((action, idx) => (
              <li key={idx}>{action}</li>
            ))}
          </ul>
        ) : (
          <p className="report-section-text">Not Available</p>
        )}
      </section>

      <section className="report-section">
        <h2 className="report-section-title">05 — Additional Notes</h2>
        <p className="report-section-text">{additional_notes || "Not Available"}</p>
      </section>

      <section className="report-section report-section--flag">
        <h2 className="report-section-title">06 — Missing or Unclear Information</h2>
        {missing_or_unclear_information && missing_or_unclear_information.length > 0 ? (
          <ul className="report-list">
            {missing_or_unclear_information.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="report-section-text">Not Available</p>
        )}
      </section>
    </div>
  );
}
