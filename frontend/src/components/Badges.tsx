type BadgeProps = {
  value: string;
};

export function CaseStatusBadge({ value }: BadgeProps) {
  return <span className={`badge status-${normalize(value)}`}>{value}</span>;
}

export function RiskBadge({ value }: BadgeProps) {
  return <span className={`badge risk-${normalize(value)}`}>{value}</span>;
}

function normalize(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}
