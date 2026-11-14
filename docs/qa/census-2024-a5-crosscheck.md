# Cross-check: DCS table A5 against the release's sex and age values

Prepared by an agent for the lead, 2026-11-14. Verification tags: ✅ checked here · 🟡 claimed,
not checked · ❌ not done or failed · ❓ assumption.

## Why

The release's DS, district and national population, sex and age values
(`census-2024-gnd-tables`) are sums of GN rows from DCS's GN population workbook. DCS also
publishes **table A5** (Population A-series): population by sex and four age bands for every DS
division and district, as its own lines. A5 is already snapshotted (`PopulationA_A5.xlsx`,
sha256 `878d35a9f7b3…`), so it is an independent check on our sums that costs nothing to run. A5
is used here as a check only; none of its values are published.

## Result ✅

Release `v2026.11.10-preview.2`; script
[`data/census-2024-a5-crosscheck.py`](data/census-2024-a5-crosscheck.py). DS lines join through the
reviewed match file `dcs-census2024-population-a-series-ds.csv` and the G02 crosswalk.

| | Lines | Values compared | Differ |
|---|---|---|---|
| Total, male, female | 365 (Sri Lanka, 25 districts, 339 DS) | 1,095 | **0** |
| Age: under 15, 15–59, 60–64, 65 and over | 365 | 1,460 | **30** |

DCS 5224 Kalmunai is skipped (no spine unit, D-022).

The 30 age differences:

- are in **8 DS divisions** and the **5 districts** that contain them (Colombo, Gampaha, Kandy,
  Hambantota, Badulla);
- net to **zero in every place**: people move between two neighbouring bands, never in or out;
- sit only on the **15 and 65 boundaries** (under 15 ↔ 15–59, 60–64 ↔ 65 and over);
- are at most **4 people** (Colombo district: A5 has 4 more under 15 and 4 fewer aged 15–59);
- vanish at national level: the Sri Lanka lines agree.

| Place | Under 15 | 15–59 | 60–64 | 65+ (release − A5) |
|---|---|---|---|---|
| Colombo district (LK11) | +4 | −4 | −1 | +1 |
| Colombo DS (LK1103) | +3 | −3 | +1 | −1 |
| Kaduwela (LK1109) | +1 | −1 | | |
| Maharagama (LK1121) | | | −2 | +2 |
| Gampaha district (LK12), Mirigama (LK1212) | −1 | +1 | | |
| Kandy district (LK21) | −2 | +2 | | |
| Minipe (LK2121), Harispattuwa (LK2133) | −1 | +1 | | |
| Hambantota district (LK33), Hambantota DS (LK3312) | −1 | +1 | | |
| Badulla district (LK81), Mahiyanganaya (LK8103) | | | +1 | −1 |

## Which source is right?

Not ours to decide ❓, but DCS's two GN files agree with each other: in every place above, the
GN population workbook's broad bands equal the sums of the GN **five-year** age file
(`census-2024-topic-tables`) exactly ✅. So the GN data are internally consistent, and A5 differs
from both. A likely reading is that A5 was tabulated from a slightly different age variable or
edit (for example age at a different reference date) ❓.

**The release keeps the GN sums.** They are what every published value traces to, and they agree
with the second GN file. This is recorded as a known difference between DCS publications, not a
correction.

## Not checked

- Population A1 (the same figures for districts only) was not compared separately; A5's 25
  district lines cover it ❓.
- No comparison with the Final Report's age tables by DS ❌.
