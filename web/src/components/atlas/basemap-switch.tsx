"use client";

import { BASEMAPS, type Basemap } from "@/lib/atlas/basemap";

export default function BasemapSwitch({
  value,
  onChange,
}: {
  value: Basemap;
  onChange: (next: Basemap) => void;
}) {
  return (
    <div className="basemap-switch" role="radiogroup" aria-label="Basemap">
      {BASEMAPS.map((item) => (
        <button
          key={item.id}
          type="button"
          role="radio"
          aria-checked={value === item.id}
          className={value === item.id ? "is-active" : undefined}
          onClick={() => onChange(item.id)}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
