import { expect, test } from "@playwright/test";

test("about page states the promise and shows the national total", async ({ page }) => {
  await page.goto("/about");
  await expect(
    page.getByRole("heading", {
      name: /Every place in Sri Lanka, every number about it, with its source/i,
    }),
  ).toBeVisible();
  await expect(page.getByText("21,781,800")).toBeVisible();
  await expect(page.getByText(/Private preview, not for publication/i)).toBeVisible();
});

// The atlas needs the bundle from `slf atlas export`; the CI fixture has none and shows the
// plain summary instead. Each atlas test checks which one it got.
async function hasAtlas(page: import("@playwright/test").Page): Promise<boolean> {
  await page.goto("/");
  return (await page.locator(".atlas").count()) > 0;
}

test("home opens on the map, or on the readable summary without the atlas bundle", async ({
  page,
}) => {
  if (await hasAtlas(page)) {
    await expect(page.getByRole("tab", { name: "Geography" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await expect(page.getByRole("heading", { level: 2, name: "Sri Lanka" })).toBeVisible();
    await expect(page.getByText(/Contains 9 provinces/i)).toBeVisible();
  } else {
    await expect(page.getByText("21,781,800")).toBeVisible();
  }
  await expect(page.getByText(/Private preview, not for publication/i)).toBeVisible();
});

test("atlas: a district shows its value against neighbours, parent and country", async ({
  page,
}) => {
  test.skip(!(await hasAtlas(page)), "no atlas bundle for this release");
  await page.goto("/?place=LK11");
  const panel = page.getByRole("complementary", { name: "Selected place" });
  await expect(panel.getByRole("heading", { level: 2 })).toHaveText("Colombo");
  await expect(panel.getByText("Compared to where?")).toBeVisible();
  await expect(panel.getByText(/median of 4/)).toBeVisible();
  await expect(panel.getByText(/1st highest of 25 districts/)).toBeVisible();
  // Hierarchy: up through the trail, down through the list of DS divisions.
  await expect(panel.getByRole("button", { name: "Western" })).toBeVisible();
  await panel.getByRole("button", { name: /^Dehiwala/ }).click();
  await expect(panel.getByRole("heading", { level: 2 })).toHaveText("Dehiwala");
  await expect(page).toHaveURL(/place=LK11\d\d/);
  // Every fact opens to its source.
  await panel.getByText("Sources for these numbers").click();
  await expect(panel.getByText(/sha256 [0-9a-f]{16}/).first()).toBeVisible();
});

test("atlas: similar places are explained, and a pair's distance splits into axis shares", async ({
  page,
}) => {
  test.skip(!(await hasAtlas(page)), "no atlas bundle for this release");
  await page.goto("/?place=LK1127&lens=profile");
  const panel = page.getByRole("complementary", { name: "Selected place" });
  await expect(panel.getByText("Places like this")).toBeVisible();
  const first = panel.locator(".place-list-similar li").first();
  await expect(first).toContainText(/Alike in .+; differs most in/);
  await first.getByRole("button").click();
  await expect(panel.getByText("Where the distance comes from, axis by axis")).toBeVisible();
  const shares = await panel.locator(".axis-table tbody td:last-child").allTextContents();
  const total = shares.reduce((sum, text) => sum + Number(text.replace("%", "")), 0);
  expect(Math.abs(total - 100)).toBeLessThanOrEqual(3);
});

test("atlas: the change and landscape lenses say what they have and what they lack", async ({
  page,
}) => {
  test.skip(!(await hasAtlas(page)), "no atlas bundle for this release");
  await page.goto("/?place=LK1103&lens=change");
  const panel = page.getByRole("complementary", { name: "Selected place" });
  await expect(panel.getByText(/comparison\./i)).toBeVisible();
  await page.getByRole("tab", { name: "Landscape" }).click();
  await expect(panel.getByText(/No landscape dataset is in this release/)).toBeVisible();
});

test("search finds a district and opens its place page", async ({ page }) => {
  await page.goto("/about");
  const search = page.getByRole("combobox", { name: "Search for a place" });
  await search.fill("Colombo");
  const result = page.getByRole("option").first();
  await expect(result).toContainText("Colombo");
  await result.getByRole("link").click();
  await expect(page).toHaveURL(/\/place\/LK11$/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Colombo");
  await expect(page.getByText("2,375,415").first()).toBeVisible();
});

test("atlas: search selects the place on the map", async ({ page }) => {
  test.skip(!(await hasAtlas(page)), "no atlas bundle for this release");
  const search = page.getByRole("combobox", { name: "Search for a place" });
  await search.fill("Kandy");
  await page.getByRole("option").first().getByRole("link").click();
  await expect(page).toHaveURL(/place=LK21/);
  await expect(
    page.getByRole("complementary", { name: "Selected place" }).getByRole("heading", { level: 2 }),
  ).toHaveText("Kandy");
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

test.describe("ethnicity and religion (D-036)", () => {
  test("DS page lists them in DCS's order and links each category to its indicator page", async ({
    page,
  }) => {
    await page.goto("/place/LK1103");
    const section = page.locator("#ethnicity-religion");
    await expect(section.getByRole("heading", { name: "Ethnic group and religion" })).toBeVisible();
    // Colombo DS, PopulationA_A6.xlsx row 13, column H
    const burgher = section.getByRole("row", { name: /^Burgher/ });
    await expect(burgher).toContainText("1,401");
    // DCS column order, not sorted by value: Sinhalese first although Moor/Muslim is larger here
    await expect(section.locator("tbody th").first()).toHaveText("Sinhalese");
    await expect(
      section.locator('a[href="/indicator/population_ethnicity_burgher_share"]'),
    ).toHaveCount(1);
  });

  test("they have an indicator page and appear in the list", async ({ page }) => {
    await page.goto("/indicator/population_religion_hindu_share");
    await expect(page.getByText("District distribution")).toBeVisible();
    await page.goto("/indicators");
    await expect(page.getByRole("link", { name: /Religion: Hindu|Hindu/ }).first()).toBeAttached();
  });

  test("GN pages do not show them and the drill-down stops at DS", async ({ page }) => {
    await page.goto("/place/LK1103005");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.locator("#ethnicity-religion")).toHaveCount(0);
    await page.goto("/indicators?i=population_religion_hindu_share&a=LK1103");
    await expect(page.getByText(/not published at gn division level/i)).toBeVisible();
  });
});

test("indicators page drills down to GN divisions with charts and a table", async ({ page }) => {
  // The CI fixture keeps only the Colombo DS (LK1103), so start there.
  await page.goto("/indicators?i=population_total&a=LK1103");
  await expect(page.getByRole("heading", { name: /GN divisions in Colombo/ })).toBeVisible();
  await expect(page.getByRole("img", { name: /by gn division in Colombo/i })).toBeVisible();
  await page.getByText("Show as table").click();
  await expect(page.getByRole("columnheader", { name: /GN division/ })).toBeVisible();
});

test("indicators page still lists every indicator without JavaScript", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto("/indicators");
  await expect(page.getByRole("heading", { name: "All indicators" })).toBeVisible();
  await expect(page.getByRole("link", { name: /Total population/ }).first()).toBeVisible();
  await context.close();
});

test("indicators page shows a pie of the whole for share indicators", async ({ page }) => {
  await page.goto("/indicators?i=households_water_tube_well_share&a=LK1103");
  await expect(page.getByRole("img", { name: /drinking water in Colombo/i })).toBeVisible();
  await expect(page.getByText(/the shares add to 100\.0%/)).toBeVisible();
  await page.getByText("Show pie as table").click();
  await expect(page.getByRole("columnheader", { name: /Share \(%\)/ })).toBeVisible();
});

test("DS profile compares on 25 values and names ethnic group or religion among the reasons (D-037)", async ({
  page,
}) => {
  await page.goto("/place/LK1103");
  const profile = page.locator("#profile");
  await expect(profile).toContainText("25 census values");
  await expect(profile).toContainText(/Ethnic group|Religion/);
  await page.goto("/place/LK1103005");
  await expect(page.locator("#profile")).toContainText("nine census values");
});
