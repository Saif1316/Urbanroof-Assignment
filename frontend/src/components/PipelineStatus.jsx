const STEPS = [
  { key: "extracting", label: "Extracting" },
  { key: "analyzing", label: "Analyzing" },
  { key: "merging", label: "Merging" },
  { key: "ready", label: "Report Ready" },
];

function stepState(stepKey, currentStage) {
  const order = ["idle", "extracting", "analyzing", "merging", "ready"];
  const currentIndex = order.indexOf(currentStage);
  const stepIndex = order.indexOf(stepKey);
  if (currentStage === "error") return "idle";
  if (stepIndex < currentIndex) return "done";
  if (stepIndex === currentIndex) return "active";
  return "idle";
}

export default function PipelineStatus({ stage }) {
  return (
    <div className="pipeline" aria-label="Generation pipeline status">
      <div className="pipeline-track">
        {STEPS.map((step, i) => {
          const state = stepState(step.key, stage);
          return (
            <div className="pipeline-step" key={step.key}>
              <div className={`pipeline-node pipeline-node--${state}`}>
                {state === "done" ? "✓" : i + 1}
              </div>
              <span className={`pipeline-label pipeline-label--${state}`}>
                {step.label}
              </span>
              {i < STEPS.length - 1 && (
                <div className={`pipeline-line pipeline-line--${state}`} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
