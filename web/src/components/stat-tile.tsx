import Link from "next/link";

type StatTileProps = {
  label: string;
  value: string;
  note?: string;
  href?: string;
};

export default function StatTile({ label, value, note, href }: StatTileProps) {
  const body = (
    <>
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
      {note ? <span className="stat-note">{note}</span> : null}
    </>
  );
  return href ? (
    <Link className="stat" href={href}>
      {body}
    </Link>
  ) : (
    <div className="stat">{body}</div>
  );
}
