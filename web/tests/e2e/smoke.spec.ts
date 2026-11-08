import { expect, test } from "@playwright/test";

test("home page states the promise and shows the national total", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: /Every place in Sri Lanka, every number about it, with its source/i,
    }),
  ).toBeVisible();
  await expect(page.getByText("21,781,800")).toBeVisible();
  await expect(page.getByText(/Private preview, not for publication/i)).toBeVisible();
});

test("search finds a district and opens its place page", async ({ page }) => {
  await page.goto("/");
  const search = page.getByRole("combobox", { name: "Search for a place" });
  await search.fill("Colombo");
  const result = page.getByRole("option").first();
  await expect(result).toContainText("Colombo");
  await result.getByRole("link").click();
  await expect(page).toHaveURL(/\/place\/LK11$/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Colombo");
  await expect(page.getByText("2,375,415").first()).toBeVisible();
});

test("explore page has a table that works without the map", async ({ page }) => {
  await page.goto("/explore?indicator=population_total&level=district");
  await expect(page.getByRole("heading", { name: "Census Atlas 2024" })).toBeVisible();
  await expect(page.getByText(/View as table/)).toBeVisible();
  await expect(page.getByRole("link", { name: "Colombo" }).first()).toBeVisible();
  await expect(page.getByText("2,375,415").first()).toBeVisible();
});

test("place page shows provenance and child areas", async ({ page }) => {
  await page.goto("/place/LK11");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Colombo");
  await expect(page.getByText("2,375,415").first()).toBeVisible();
  await expect(
    page.getByRole("heading", { name: /13 divisional secretariats/i }),
  ).toBeVisible();
  await page.locator("details.provenance summary").first().click();
  await expect(page.getByText("Snapshot sha256").first()).toBeVisible();
  await expect(page.getByText(/machine extracted/i).first()).toBeVisible();
});

test("indicator page shows the national value and district distribution", async ({
  page,
}) => {
  await page.goto("/indicator/population_density");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Population density");
  await expect(page.getByText("District distribution")).toBeVisible();
  await expect(page.getByText(/per km²/).first()).toBeVisible();
});

test("data page explains the block and lists checksums", async ({ page }) => {
  await page.goto("/data");
  await expect(
    page.getByRole("heading", { name: "Release contents and static API" }),
  ).toBeVisible();
  await expect(page.getByText(/not downloadable publicly/i)).toBeVisible();
  await expect(page.getByText("CHECKSUMS.sha256", { exact: true })).toBeVisible();
  await expect(page.getByText("observations/census-2024-gnd-tables.parquet")).toBeVisible();
});

test("methods page states what was not checked", async ({ page }) => {
  await page.goto("/methods");
  await expect(
    page.getByRole("heading", { name: /How this atlas is built/ }),
  ).toBeVisible();
  await expect(page.getByText(/No human has spot-checked GN cells/)).toBeVisible();
});

test("static API carries the preview flag and provenance", async ({ request }) => {
  const response = await request.get("/api/v1/places/LK11.json");
  expect(response.ok()).toBe(true);
  const body = await response.json();
  expect(body.publishable).toBe(false);
  expect(body.release).toBe("v2026.11.4-preview.1");
  expect(body.values.length).toBe(14);
  expect(body.values[0].snapshot_sha256).toMatch(/^[0-9a-f]{64}$/);
});
