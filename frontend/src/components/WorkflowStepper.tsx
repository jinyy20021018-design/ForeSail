import type { WorkflowState } from "../api/client";

type Props = {
  workflow: WorkflowState | null;
};

export function WorkflowStepper({ workflow }: Props) {
  if (!workflow) return null;
  return (
    <section className="panel full-width">
      <div className="panel-heading">
        <h2>Workflow Stepper</h2>
        <span className="tag">{workflow.current_step}</span>
      </div>
      <div className="stepper">
        {workflow.steps.map((step, index) => (
          <div className={`step step-${step.status.toLowerCase()}`} key={step.name}>
            <b>{index + 1}. {step.name}</b>
            <span>{step.status}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
