# Null-name GN divisions: evidence for D-028

Prepared 2026-11-12 by an agent for the lead's review. Hand-written; the crosswalk build does not
regenerate this file. Per-unit evidence: [`null-name-gns.csv`](null-name-gns.csv) (65 rows).

Verification tags: ✅ verified by running or reading the cited source · 🟡 claimed by a source,
not independently checked · ❌ not found or failed · ❓ assumption.

## Summary

COD-AB v03 has **65 GN divisions with no English, Sinhala or Tamil name** ✅ (spine build,
`level == 4` and all three names null). D-028 keeps them as p-code labels for 1A and asks for
names to be resolved through crosswalk review before 1B.

| Category | GNs | What we hold | Recommendation |
|---|---|---|---|
| A. DCS 2024 and NSDI 2017 agree on the English name | 8 | English name in both; Sinhala gazetted name in NSDI | Promote, recording both sources |
| B. DCS 2024 only | 4 | English name in DCS only | Promote English, labelled single-source |
| C. Kalmunai, COD-AB `LK5221150`–`LK5221300` | 29 | DCS 5224 lists 29 names, but which name goes with which unit is unknown | Keep p-code labels (D-022) |
| D. Eravur Pattu, `LK5115` | 7 | 3 unmatched DCS/NSDI GNs, flagged by NSDI as a disputed boundary | Keep p-code labels |
| E. No candidate in any held source | 17 | Nothing; mostly very small units | Keep p-code labels |

## A correction found while doing this: Kandalama and Kiralessa were swapped

This affects one of the 22 matches the lead accepted on 2026-11-12, which the agent had
recommended. It is corrected in this branch, pending the lead's review.

Before the correction:

- DCS 2206125 **Kandalama** joined COD-AB `LK2206125`, an unnamed unit. This was an automatic
  match on the code alone.
- DCS 2206265 **Kiralessa** joined COD-AB `LK2206300`, which COD-AB names "Kandalama". This
  was the lead's manual match.

Evidence that the two were swapped:

1. **Location** ✅. OpenStreetMap Nominatim places Kandalama village at 7.8954 N, 80.7045 E.
   That point falls inside `LK2206300`. `LK2206125` is 12.6 km away.
2. **GN numbers** ✅ (NSDI 2017 attribute snapshot). Kandalama is GN **E449** and Kiralessa is
   **E441C**.
   - Neighbours of `LK2206300`: Inamaluwa E451, Pothana E452C, Nikawatawana E447, Pahala
     Erevula E446, Pelvehera E450A and others. All are in the E446–E452 range, which fits E449.
   - Neighbours of `LK2206125`: Embulambe E440, Lenadora North E441, Pannampitiya E441A, Puwak
     Attawala E441D and Walgamwewa E442A. This fits E441C.
3. **COD-AB's own name** for `LK2206300` is Kandalama.

Fix: `catalog/geographies/manual-matches.csv` now maps 2206125 Kandalama → `LK2206300` and
2206265 Kiralessa → `LK2206125`, for both DCS and NSDI. nuuuwan inherits the DCS matches. Preview
`v2026.11.6-preview.1` carries the corrected values: 28 changed values (2 GNs × 14 indicators),
0 added, 0 removed.

| | v2026.11.5 | v2026.11.6 |
|---|---|---|
| `LK2206300` (20.7 km²) population | 685 | 2,239 (Kandalama) |
| `LK2206125` (2.7 km²) population | 2,239 | 685 (Kiralessa) |

**The same test on the other 11 named candidates.** Each candidate's NSDI GN number sits inside
its neighbours' number series. For example, Aluthwatta E335C has neighbours E334B–E335A, and
Egoda Waleboda 266 has neighbours 265–265D. The four DCS-only GNs have no NSDI number to test.
This supports the matches but does not prove them ❓. Only GN geometry or an official GN list
would settle them.

## Category A: 8 GNs, two sources agree

| Spine unit | DS | English name (DCS = NSDI) | NSDI GN no. | Sinhala (NSDI gazetted) |
|---|---|---|---|---|
| `LK2206125` | Dambulla | Kiralessa | E441C | කීරලැස්ස |
| `LK2215285` | Yatawatta | Aluthwatta | E335C | අළුත්වත්ත |
| `LK2218265` | Matale | Kirigalpotta | E328C | කිරිගල්පොත්ත |
| `LK2221150` | Ambanganga | Aluthwela | E380B | අලුත්වෙල |
| `LK8215135` | Monaragala | Horombuwa | 131C | හොරොම්බුව |
| `LK8218210` | Badalkumbura | Pussellawa | 131C | පුස්සැල්ලාව |
| `LK9106080` | Kuruvita | Ekneligoda North | 159B | එක්නැලිගොඩ උතුර |
| `LK9118005` | Balangoda | Egoda Waleboda | 266 | එගොඩ වලේබොඩ |

The Sinhala names are NSDI's `gnd_name_gazetted` field, so they come from a source, not from
transliteration (D-012). Tamil names: none held.

## Category B: 4 GNs, DCS only

`LK5104005` Punanai East (Koralai Pattu Central), `LK6145226` Moragolla, `LK6145227` Rideekanda
and `LK6145228` Thengodagedara (Panduwasnuwara West).

NSDI 2017 has none of these four codes. That is consistent with GNs created after 2017 ❓.

## Category C: 29 GNs in Kalmunai

COD-AB `LK5221` holds 58 GNs:

- **29 named GNs.** These are exactly DCS 5221 Kalmunai North Sub, which already has the
  provisional unit `LK-ADM3-P0001` (D-022).
- **29 unnamed GNs**, `LK5221150`–`LK5221300`. DCS 5224 Kalmunai also has 29 GNs, but nothing
  links a DCS name to a particular COD-AB unit, and NSDI 2017 has no unmatched GN in that DS.

This stays blocked under D-022 until an official GN list with numbers, or GN geometry, arrives.

## Category D: 7 GNs in Eravur Pattu

COD-AB `LK5115` has 7 unnamed GNs (`…006`, `…014`, `…016`, `…200`, `…210`, `…215`, `…235`).

DCS and NSDI each have 3 GNs in the DS that did not match: Eravur 04 (5115010), Eravur 05
(5115075) and Ellainagar (5115005). NSDI marks all three "GN boundary dispute with Gap" ✅.

With 7 units against 3 names and a recorded dispute, no assignment can be made from these
sources. The site describes the area neutrally (AGENTS rule 12).

## Category E: 17 GNs with no candidate

None of these units has a row in DCS 2024 or NSDI 2017 ✅:

- `LK4130000` (Thenmaradchi)
- `LK5104002`, `LK5104003`, `LK5104004`, `LK5104013` (Koralai Pattu Central)
- `LK5109012`, `LK5109021`, `LK5109022`, `LK5109065` (Koralai Pattu)
- `LK5124009`, `LK5124017` (Kattankudy)
- `LK5127018` (Manmunai Pattu)
- `LK5130011` (Manmunai South West)
- `LK5133019` (Porativu Pattu)
- `LK5136230`, `LK5136235` (Manmunai South & Eruvil Pattu)
- `LK5139007` (Eravur Town)

The median area is 0.14 km². Nine are under 0.1 km², and the smallest is 0.009 km² (about one
hectare) ✅. Several codes break COD-AB's usual 5-step numbering (`…002`, `…003`, `…004`), and
one ends in `000`. That suggests these may be digitising artefacts or slivers rather than real GN
divisions ❓. We hold no source that can confirm this.

## Decisions needed from the lead

1. **Kandalama/Kiralessa correction.** Accept it? Recommendation: yes. Merging this PR applies
   it.
2. **Category A (8).** Promote the English names, plus the NSDI Sinhala gazetted names, into the
   spine through `overrides/`, with the name source recorded? Recommendation: yes. Two
   independent public sources agree, and a name is a low-risk fact. Both sources' reuse rights
   are still `unclear`, so the override records that.
3. **Category B (4).** Promote the English names from DCS alone, labelled single-source?
   Recommendation: yes. The alternative is to keep p-codes until a second source appears.
4. **Categories C, D and E (53).** Keep the p-code labels and add a question about GN lists to a
   later DCS or Survey Department follow-up (agents draft; the lead sends). Recommendation: yes.
   This does not block 1B, because D-028 is met once the resolvable names are resolved and the
   rest are recorded as unresolvable from current sources.
