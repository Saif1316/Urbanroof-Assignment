import SeverityBadge from "./SeverityBadge";

export default function AreaObservationCard({ area }) {
  const {
    area_name,
    observation,
    probable_root_cause,
    severity,
    severity_reasoning,
    recommended_action,
    image_data_uri,
    image_caption,
  } = area;

  return (
    <article className="area-card">
      <div className="area-card-header">
        <h3 className="area-card-title">{area_name || "Not Available"}</h3>
        <SeverityBadge level={severity} />
      </div>

      <div className="area-card-body">
        <div className="area-card-text">
          <dl className="area-detail-list">
            <dt>Observation</dt>
            <dd>{observation || "Not Available"}</dd>

            <dt>Probable Root Cause</dt>
            <dd>{probable_root_cause || "Not Available"}</dd>

            <dt>Severity Reasoning</dt>
            <dd>{severity_reasoning || "Not Available"}</dd>

            <dt>Recommended Action</dt>
            <dd>{recommended_action || "Not Available"}</dd>
          </dl>
        </div>

        <div className="area-card-image">
          {image_data_uri ? (
            <>
              <img src={image_data_uri} alt={image_caption || area_name} />
              {image_caption && (
                <span className="area-card-image-caption">{image_caption}</span>
              )}
            </>
          ) : (
            <div className="area-card-image-missing">
              <span>Image Not Available</span>
            </div>
          )}
        </div>
      </div>
    </article>
  );
}
