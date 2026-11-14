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
  // The count depends on the release: 13 in the full preview, 1 in the CI fixture
  // (which keeps only the Colombo DS, LK1103). Check the heading's form and that child.
  await expect(
    page.getByRole("heading", { name: /^\d+ divisional secretariats?$/i }),
  ).toBeVisible();
  await expect(page.locator('a[href="/place/LK1103"]').first()).toBeVisible();
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
  expect(body.release).toMatch(/^v\d{4}\.\d{1,2}\.\d+-preview\.\d+$/);
  expect(body.values.length).toBeGreaterThan(14);
  expect(body.values[0].snapshot_sha256).toMatch(/^[0-9a-f]{64}$/);
});

test.describe("without JavaScript (D-027)", () => {
  test.use({ javaScriptEnabled: false });

  test("explore shows a server-rendered table", async ({ page }) => {
    await page.goto("/explore");
    await expect(
      page.getByRole("heading", { level: 1, name: /^Population density by district$/i }),
    ).toBeVisible();
    await expect(page.getByRole("link", { name: "Colombo" }).first()).toBeVisible();
    await expect(page.getByText(/per km²/).first()).toBeVisible();
    await expect(page.getByText("Loading explorer")).toHaveCount(0);
  });

  test("place and indicator pages show their content, not a loading placeholder", async ({
    page,
  }) => {
    await page.goto("/place/LK11");
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Colombo");
    await expect(page.getByText("2,375,415").first()).toBeVisible();
    await expect(page.getByText("Loading place")).toHaveCount(0);
    await page.goto("/indicator/population_density");
    await expect(page.getByRole("heading", { level: 1 })).toContainText("Population density");
  });

  test("table pages link to each other and show values", async ({ page }) => {
    await page.goto("/explore");
    await page.getByRole("link", { name: "Total population" }).first().click();
    await expect(page).toHaveURL(/\/explore\/table\/population_total\/district$/);
    await expect(page.getByText("2,375,415").first()).toBeVisible();
    await page.getByRole("link", { name: "Provinces" }).click();
    await expect(page).toHaveURL(/\/explore\/table\/population_total\/province$/);
    await expect(page.getByRole("link", { name: "Western" }).first()).toBeVisible();
  });
});

test.describe("ethnicity and religion (D-033)", () => {
  test("DS page shows them in their own section, in DCS's order, without indicator links", async ({
    page,
  }) => {
    await page.goto("/place/LK1103");
    const section = page.locator("#ethnicity-religion");
    await expect(section.getByRole("heading", { name: "Ethnic group and religion" })).toBeVisible();
    // Colombo DS, PopulationA_A6.xlsx row 13, column H
    const burgher = section.getByRole("row", { name: /^Burgher/ });
    await expect(burgher).toContainText("1,401");
    // DCS column order, never sorted by value: Sinhalese first although Moor/Muslim is larger here
    await expect(section.locator("tbody th").first()).toHaveText("Sinhalese");
    await expect(page.locator('a[href^="/indicator/population_ethnicity"]')).toHaveCount(0);
    await expect(page.locator('a[href^="/indicator/population_religion"]')).toHaveCount(0);
  });

  test("GN pages do not show them and they have no indicator page", async ({ page }) => {
    await page.goto("/place/LK1103005");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.locator("#ethnicity-religion")).toHaveCount(0);
    // No indicator page: Next.js streams its not-found view (with status 200 here, as for any
    // unknown indicator id).
    await page.goto("/indicator/population_religion_hindu_share");
    await expect(page.getByText("This page could not be found.")).toBeVisible();
    await expect(page.getByText("District distribution")).toHaveCount(0);
    // Missing pages are served with status 200 under Cache Components, so they must not be indexed
    await expect(page.locator('meta[name="robots"][content="noindex"]').first()).toBeAttached();
  });
});
