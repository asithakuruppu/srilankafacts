import type { Observation } from "@/lib/types";

export default function Provenance({ value }: { value: Observation }) {
  return (
    <details className="provenance" id={`provenance-${value.indicator_id}`}>
      <summary>Source</summary>
      <dl>
        <div>
          <dt>Source</dt>
          <dd>Department of Census and Statistics, Census of Population and Housing 2024</dd>
        </div>
        <div>
          <dt>Locator</dt>
          <dd>{value.source_locator}</dd>
        </div>
        <div>
          <dt>Snapshot sha256</dt>
          <dd>
            <code>{value.snapshot_sha256}</code>
          </dd>
        </div>
        <div>
          <dt>Reference date</dt>
          <dd>
            {value.time_start}
            {value.time_end !== value.time_start ? ` to ${value.time_end}` : ""}
          </dd>
        </div>
        <div>
          <dt>Period</dt>
          <dd>{value.period}</dd>
        </div>
        <div>
          <dt>Support</dt>
          <dd>{value.support_type}</dd>
        </div>
        <div>
          <dt>Verification</dt>
          <dd>{value.verification.replaceAll("_", " ")}</dd>
        </div>
        <div>
          <dt>Claim</dt>
          <dd>
            <code>{value.claim_id}</code>
          </dd>
        </div>
      </dl>
    </details>
  );
}
