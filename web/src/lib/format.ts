const numberFormatters = new Map<number, Intl.NumberFormat>();

function formatter(decimals: number): Intl.NumberFormat {
  const cached = numberFormatters.get(decimals);
  if (cached) {
    return cached;
  }
  const created = new Intl.NumberFormat("en-LK", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  numberFormatters.set(decimals, created);
  return created;
}

const UNIT_DECIMALS: Record<string, number> = {
  percent: 1,
  "persons per km2": 1,
  "persons per housing unit": 2,
  "males per 100 females": 1,
  housing_units: 0,
  persons: 0,
};

const UNIT_SUFFIX: Record<string, string> = {
  percent: "%",
  "persons per km2": " per km²",
  "persons per housing unit": " per occupied unit",
  "males per 100 females": " males per 100 females",
  housing_units: " units",
};

export function decimalsFor(unit: string): number {
  return UNIT_DECIMALS[unit] ?? 0;
}

export function formatNumber(value: number, decimals = 0): string {
  return formatter(decimals).format(value);
}

export function formatValue(
  value: number | null | undefined,
  unit: string,
  decimals?: number,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "Not available";
  }
  const places = decimals ?? decimalsFor(unit);
  const suffix = UNIT_SUFFIX[unit] ?? "";
  return `${formatter(places).format(value)}${suffix}`;
}

export function formatCompact(value: number): string {
  return new Intl.NumberFormat("en-LK", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

export function formatDelta(value: number, unit: string, reference: number): string {
  const difference = value - reference;
  if (unit === "percent") {
    const sign = difference >= 0 ? "+" : "−";
    return `${sign}${formatNumber(Math.abs(difference), 1)} pp vs national`;
  }
  if (reference === 0) {
    return "no national base";
  }
  const percent = (100 * difference) / reference;
  const sign = percent >= 0 ? "+" : "−";
  return `${sign}${formatNumber(Math.abs(percent), 1)}% vs national`;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 ** 2) {
    return `${(bytes / 1024).toFixed(0)} KB`;
  }
  if (bytes < 1024 ** 3) {
    return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  }
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}

export function formatDate(iso: string): string {
  const date = new Date(`${iso}T00:00:00Z`);
  return new Intl.DateTimeFormat("en-LK", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(date);
}

export function levelLabel(level: string): string {
  const labels: Record<string, string> = {
    country: "Country",
    province: "Province",
    district: "District",
    ds: "Divisional Secretariat",
    "ds-provisional": "Divisional Secretariat (provisional)",
    gn: "Grama Niladhari division",
  };
  return labels[level] ?? level;
}
