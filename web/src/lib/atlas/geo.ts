/** Small planar and spherical helpers for the area tool and the point resolver. */

import type { Geometry } from "@/lib/atlas/types";

export type LonLat = [number, number];
export type Box = [number, number, number, number];

const EARTH_RADIUS_KM = 6371.0088;

/** Great-circle distance in kilometres. */
export function distanceKm(a: LonLat, b: LonLat): number {
  const rad = Math.PI / 180;
  const dLat = (b[1] - a[1]) * rad;
  const dLon = (b[0] - a[0]) * rad;
  const h =
    Math.sin(dLat / 2) ** 2 + Math.cos(a[1] * rad) * Math.cos(b[1] * rad) * Math.sin(dLon / 2) ** 2;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.min(1, Math.sqrt(h)));
}

/** Ray casting on one ring (closed or not). Points exactly on an edge may fall either way. */
export function inRing(point: LonLat, ring: number[][]): boolean {
  let inside = false;
  const [x, y] = point;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) {
      inside = !inside;
    }
  }
  return inside;
}

/** A polygon's outer ring contains the point and none of its holes do. */
export function inPolygon(point: LonLat, rings: number[][][]): boolean {
  if (rings.length === 0 || !inRing(point, rings[0])) {
    return false;
  }
  return !rings.slice(1).some((hole) => inRing(point, hole));
}

export function inGeometry(point: LonLat, geometry: Geometry): boolean {
  if (geometry.type === "Polygon") {
    return inPolygon(point, geometry.coordinates);
  }
  if (geometry.type === "MultiPolygon") {
    return geometry.coordinates.some((rings) => inPolygon(point, rings));
  }
  return false;
}

export function boxOf(points: LonLat[]): Box {
  let [w, s, e, n] = [Infinity, Infinity, -Infinity, -Infinity];
  for (const [x, y] of points) {
    w = Math.min(w, x);
    s = Math.min(s, y);
    e = Math.max(e, x);
    n = Math.max(n, y);
  }
  return [w, s, e, n];
}

export function boxesOverlap(a: Box, b: Box): boolean {
  return a[0] <= b[2] && b[0] <= a[2] && a[1] <= b[3] && b[1] <= a[3];
}

/** A circle as a closed ring of `steps` points, for drawing. */
export function circleRing(centre: LonLat, radiusKm: number, steps = 96): number[][] {
  const lat = (centre[1] * Math.PI) / 180;
  const dLat = (radiusKm / EARTH_RADIUS_KM) * (180 / Math.PI);
  const dLon = dLat / Math.cos(lat);
  const ring: number[][] = [];
  for (let i = 0; i <= steps; i++) {
    const t = (2 * Math.PI * i) / steps;
    ring.push([centre[0] + dLon * Math.cos(t), centre[1] + dLat * Math.sin(t)]);
  }
  return ring;
}

/** The bounding box of a circle, generous by a little so no cell is missed. */
export function circleBox(centre: LonLat, radiusKm: number): Box {
  return boxOf(circleRing(centre, radiusKm * 1.01, 32) as LonLat[]);
}
