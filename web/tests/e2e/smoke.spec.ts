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

test("landscape: a layer is mapped with its floor, and a GN lists what is here", async ({ page }) => {
  const index = await page.request.get("/release/atlas/landscape/index.json");
  test.skip(!index.ok(), "this build has no landscape layers");
  await page.goto("/?place=LK2130120&lens=landscape");
  await expect(page.getByText("Measured from satellite and open map data")).toBeVisible();
  await expect(page.locator(".atlas-legend")).toContainText("modelled estimate");
  const features = await page.request.get("/release/atlas/features/LK21.json");
  if (features.ok()) {
    await expect(page.getByTestId("whats-here")).toContainText("What is here");
    await expect(page.getByTestId("whats-here")).not.toContainText("bombing");
  }
});

test("areas: a radius around Colombo gives a labelled estimate, and a point resolves to its places", async ({
  page,
}) => {
  const grid = await page.request.get("/release/atlas/grid/LK11.json");
  test.skip(!grid.ok(), "this build has no analytic grid");
  await page.goto("/area?lon=79.86120&lat=6.92710&r=3&ind=population_total");
  await expect(page.getByTestId("area-estimate")).toContainText("≈");
  await expect(page.getByText("modelled estimate", { exact: true })).toBeVisible();
  await page.getByRole("radio", { name: "What is here" }).click();
  const map = page.locator(".area-map");
  const box = await map.boundingBox();
  if (!box) {
    throw new Error("no map");
  }
  // The map is fitted to the circle, so its centre is in Colombo.
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  await expect(page.getByTestId("resolver-table")).toContainText("LK11");
  await expect(page.getByTestId("resolver-table")).toContainText("LK-ED-01");
});

test("atlas: a district shows its 2012 to 2024 total as the sum of its DS divisions", async ({
  page,
}) => {
  test.skip(!(await hasAtlas(page)), "no atlas bundle for this release");
  await page.goto("/?place=LK11&lens=change");
  const history = await page.request.get("/release/atlas/change.json");
  test.skip(!history.ok(), "this bundle has no census history");
  const total = page.getByTestId("change-area-total");
  await expect(total).toContainText("the sum of");
  await expect(total).toContainText("DS divisions");
});

test("atlas: the change and landscape lenses say what they have and what they lack", async ({
  page,
}) => {
  test.skip(!(await hasAtlas(page)), "no atlas bundle for this release");
  await page.goto("/?place=LK1103&lens=change");
  const panel = page.getByRole("complementary", { name: "Selected place" });
  await expect(panel.getByText(/comparison\./i)).toBeVisible();
  await page.getByRole("tab", { name: "Landscape" }).click();
  await expect(
    panel.getByText(/This build has no landscape layers|Measured from satellite and open map data/),
  ).toBeVisible();
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

async function hasElections(page: import("@playwright/test").Page): Promise<boolean> {
  if (!(await hasAtlas(page))) {
    return false;
  }
  const response = await page.request.get("/release/meta.json");
  const meta = (await response.json()) as { atlas?: { electoral?: boolean } | null };
  return Boolean(meta.atlas?.electoral);
}

test("elections lens: a district becomes its electoral district, results keep ballot order", async ({
  page,
}) => {
  test.skip(!(await hasElections(page)), "no election results in this atlas bundle");
  await page.goto("/?place=LK45");
  const panel = page.getByRole("complementary", { name: "Selected place" });
  await expect(panel.getByRole("heading", { level: 2 })).toHaveText("Kilinochchi");
  await page.getByRole("tab", { name: "Elections" }).click();
  await expect(panel.getByRole("heading", { level: 2 })).toHaveText("Jaffna");
  await expect(page).toHaveURL(/place=LK-ED-10/);
  await expect(panel.getByText(/made of the districts Jaffna, Kilinochchi/)).toBeVisible();
  await expect(panel.getByText(/Polling divisions are in tables only/)).toBeVisible();
  await panel.getByText(/Votes for all \d+ candidates, in ballot-paper order/).click();
  const ballots = await panel.locator(".election-candidates tbody td:first-child").allTextContents();
  expect(ballots.map(Number)).toEqual([...ballots.map(Number)].sort((a, b) => a - b));
  // The ED scale exists; LA and MOH say why they are not drawn.
  const scale = page.getByRole("group", { name: "Geographic scale" });
  await expect(scale.getByRole("button", { name: "LA", exact: true })).toBeDisabled();
  await expect(scale.getByRole("button", { name: "MOH", exact: true })).toBeDisabled();
  await expect(scale.getByRole("button", { name: "ED", exact: true })).toBeEnabled();
  // Leaving the lens drops the ED selection rather than showing a "place not found".
  await page.getByRole("tab", { name: "Geography" }).click();
  await expect(panel.getByRole("heading", { level: 2 })).toHaveText("Sri Lanka");
});

test("election results page lists every electoral district with its source", async ({ page }) => {
  await page.goto("/elections/presidential-2024");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Presidential Election 2024");
  if (await page.getByText("No election results in this build yet.").count()) {
    return;
  }
  await expect(page.getByRole("heading", { name: "By electoral district" })).toBeVisible();
  await expect(page.locator("section.election-ed")).toHaveCount(22);
  await expect(page.getByText(/not yet verified by a person/).first()).toBeVisible();
});

async function hasSpaces(page: import("@playwright/test").Page): Promise<boolean> {
  const response = await page.request.get("/release/meta.json");
  const meta = (await response.json()) as { atlas?: { spaces?: { composite?: boolean } | null } | null };
  return Boolean(meta.atlas?.spaces?.composite);
}

test("two-map explorer: selection is linked both ways and weights recompute distances", async ({
  page,
}) => {
  test.skip(!(await hasSpaces(page)), "no vector spaces in this atlas bundle");
  await page.goto("/explore/space?place=LK1127");
  const answer = page.getByRole("region", { name: "Answer" });
  await expect(answer.getByRole("heading", { level: 2 })).toContainText("Thimbirigasyaya");
  const rows = answer.locator(".space-table tbody tr");
  await expect(rows).toHaveCount(10);
  const before = await rows.locator("th").allTextContents();
  // Similarity view -> selection (and so the map's selected ring).
  const dot = page.locator(".space-dot:not(.is-selected):not(.is-near)").first();
  const id = await dot.getAttribute("data-id");
  await dot.dispatchEvent("click");
  await expect(page).toHaveURL(new RegExp(`place=${id}`));
  await expect(page.locator(`.space-dot.is-selected[data-id="${id}"]`)).toHaveCount(1);
  // Map -> similarity view: a click on the map selects a division and rings its dot.
  const box = await page.locator(".space-map-box").boundingBox();
  if (box) {
    await page.waitForTimeout(1500);
    await page.mouse.click(box.x + box.width * 0.45, box.y + box.height * 0.55);
    await expect(page.locator(".space-dot.is-selected")).toHaveCount(1);
    const chosen = await page.locator(".space-dot.is-selected").getAttribute("data-id");
    await expect(page).toHaveURL(new RegExp(`place=${chosen}`));
  }
  // Weights: removing the identity block changes the neighbours and the URL.
  await page.goto("/explore/space?place=LK1127&w=1,1,0");
  await expect(rows).toHaveCount(10);
  const after = await rows.locator("th").allTextContents();
  expect(after).not.toEqual(before);
  // Explanations are exact shares that sum to 100%.
  await rows.first().getByRole("button", { name: "Explain" }).click();
  const shares = await page.locator(".space-reasons > ul:first-of-type li").allTextContents();
  const total = shares.reduce((sum, text) => sum + Number(text.replace(/.*: (-?\d+)%$/, "$1")), 0);
  expect(Math.abs(total - 100)).toBeLessThanOrEqual(2);
});

test("search finds a misspelt place through the text space", async ({ page }) => {
  await page.goto("/about");
  const box = page.getByRole("combobox").first();
  await box.fill("Colmbo");
  await expect(page.getByRole("option").first()).toContainText("Colombo");
});

test("release calendar lists every catalogued source with a state", async ({ page }) => {
  await page.goto("/data/calendar");
  const table = page.getByTestId("calendar-table");
  if ((await table.count()) === 0) {
    await expect(page.getByText("No calendar in this build")).toBeVisible();
    return;
  }
  await expect(table.locator("tbody tr").first()).toBeVisible();
  await expect(table).toContainText(/Held, no fixed schedule|Not held yet|Overdue|Current/);
});

test("draft translations appear only on request, under a banner", async ({ page }) => {
  await page.goto("/about");
  await expect(page.getByTestId("language-banner")).toHaveCount(0);
  await page.getByRole("combobox", { name: "Interface language" }).selectOption("si");
  await expect(page.getByTestId("language-banner")).toContainText("Machine draft translation");
  await expect(page.locator("html")).toHaveAttribute("lang", "si");
  await page.getByRole("combobox", { name: /Interface language|අතුරුමුහුණත් භාෂාව/ }).selectOption("en");
  await expect(page.getByTestId("language-banner")).toHaveCount(0);
});

test("Stage 3 indicators say they are not from the census", async ({ page }) => {
  const extra = await page.request.get("/release/atlas/extra/index.json");
  test.skip(!extra.ok(), "this build has no Stage 3 indicators");
  await page.goto("/?place=LK8&ind=mpi_headcount");
  await expect(page.getByText("not from the census")).toBeVisible();
  await expect(page.getByText(/survey estimate/i).first()).toBeVisible();
});

test("llms.txt states the citation rules", async ({ page }) => {
  const response = await page.request.get("/llms.txt");
  expect(response.ok()).toBe(true);
  expect(await response.text()).toContain("not available");
});

test("the embed map shows its legend and credit", async ({ page }) => {
  test.skip(!(await hasAtlas(page)), "no atlas bundle for this release");
  await page.goto("/embed/map?ind=population_density&level=district");
  await expect(page.getByTestId("embed-legend")).toContainText("Sri Lanka Facts");
  await expect(page.getByTestId("embed-legend")).toContainText("Non-commercial");
});

test("SQL in the browser returns rows with their source", async ({ page }) => {
  const engine = await page.request.head("/release/duckdb/duckdb-eh.wasm");
  test.skip(!engine.ok(), "this build has no DuckDB engine");
  await page.goto("/query");
  await page.getByRole("button", { name: "Run query" }).click();
  await expect(page.getByTestId("query-summary")).toContainText("rows", { timeout: 60_000 });
  await expect(page.getByTestId("query-result")).toContainText("source_locator");
});

test("the change lens shows fire detections and storm passes for a district", async ({ page }) => {
  const fires = await page.request.get("/release/atlas/events/fires.json");
  test.skip(!fires.ok(), "this build has no event timelines");
  await page.goto("/?place=LK23&lens=change");
  const events = page.getByTestId("events-timeline");
  await expect(events).toContainText("Active fire detections");
  await expect(events).toContainText("Storm tracks within 50 km");
});

test("finest view lists datasets by resolution, when the bundle has the manifest", async ({ page }) => {
  test.skip(!(await hasAtlas(page)), "no atlas bundle for this release");
  await page.goto("/resolution");
  await expect(page.getByRole("heading", { level: 1, name: /best resolution/i })).toBeVisible();
  const table = page.getByRole("table");
  test.skip((await table.count()) === 0, "bundle has no resolution manifest");
  await expect(table.getByRole("row").nth(1)).toBeVisible();
});
