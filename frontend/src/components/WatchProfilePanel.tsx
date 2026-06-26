import type { WatchProfile } from "../api/client";
import { t, translate, type Language } from "../i18n";

type Props = {
  profile: WatchProfile;
  language: Language;
};

export function WatchProfilePanel({ profile, language }: Props) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{t(language, "watchProfile")}</h2>
      </div>
      <div className="compact-list">
        <p>
          <strong>{t(language, "watchedVessel")}:</strong> {profile.watched_vessel}
        </p>
        <p>
          <strong>{t(language, "watchedPorts")}:</strong> {profile.watched_ports.join(", ")}
        </p>
        <p>
          <strong>{t(language, "routeRegions")}:</strong> {profile.watched_route_regions.join(", ")}
        </p>
        <p>
          <strong>{t(language, "riskCategories")}:</strong>{" "}
          {profile.risk_categories.map((category) => translate.exposure(language, category)).join(", ")}
        </p>
      </div>
      <ul className="rule-list">
        {profile.alert_rules.map((rule) => (
          <li key={rule}>{translate.rule(language, rule)}</li>
        ))}
      </ul>
    </section>
  );
}
