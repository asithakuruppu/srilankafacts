"""Vector spaces v2 (Phase 3): typology, trajectory, composite and text.

Every space is derived from the ledger and records ``space_id`` and ``space_version``. Distances
are similarity statements, never facts (rule 13). Each builder writes a browser file (JSON) and,
where the browser recomputes something, an ``expected_*.json`` that the web tests compare against.

- ``typology`` v1.0: k-means partition of the DS ``profile`` v0.3 vectors, with k chosen by
  silhouette among the k whose bootstrap stability (adjusted Rand index) is high enough. Cluster
  names are machine drafts from each centre's back-projected inputs.
- ``trajectory`` v0.1: DS change vectors 2012 -> 2024 (annual population growth, change in the
  sex ratio) on units with a one-to-one 2012 predecessor, carrying the history build's
  exact/approximate flag. Private under D-038: local preview only, never in a release.
- ``composite`` v0.1: the profile space with a weight per input block. Each place's axis scores
  are split exactly into block contributions (scores = sum over blocks); the browser scales the
  contributions by the reader's weights, so with all weights 1 the space *is* profile v0.3 and
  the per-axis decomposition stays exact for any weights.
- ``text`` v0.1: character 2- and 3-gram TF-IDF vectors of every place's English, Sinhala and
  Tamil names, cosine similarity, for search. No model download.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from slf import profile as pf

SEED = 20261117

TYPOLOGY_ID, TYPOLOGY_VERSION = "typology", "1.0"
TRAJECTORY_ID, TRAJECTORY_VERSION = "trajectory", "0.1"
COMPOSITE_ID, COMPOSITE_VERSION = "composite", "0.1"
TEXT_ID, TEXT_VERSION = "text", "0.1"

K_RANGE = range(3, 11)
RESTARTS = 25
BOOTSTRAP_RUNS = 50
MIN_STABILITY = 0.75  # mean adjusted Rand index of bootstrap partitions vs the full-data one
NAME_MIN_SD = 0.5  # an input must differ from the national average by this much to name a type
LABEL_STATUS = "machine_generated_draft"

TRAJECTORY_K = 10
COMPOSITE_K = 10
COMPOSITE_PRESETS: dict[str, dict[str, float]] = {
    "equal": {"demography": 1.0, "housing": 1.0, "identity": 1.0},
    "no_identity": {"demography": 1.0, "housing": 1.0, "identity": 0.0},
    "no_housing": {"demography": 1.0, "housing": 0.0, "identity": 1.0},
    "no_demography": {"demography": 0.0, "housing": 1.0, "identity": 1.0},
    "mixed": {"demography": 2.0, "housing": 1.0, "identity": 0.5},
}
BLOCK_LABELS = {
    "demography": "Population and age",
    "housing": "Housing and density",
    "identity": "Ethnic group and religion",
}
DECIMALS = 6
TEXT_K = 5


def _dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n")


# --- the DS profile fit, rebuilt from the census so blocks can be separated -----------------


def refit_ds(observations: pd.DataFrame, geographies: pd.DataFrame) -> pf.Fit:
    """Rebuild the DS profile fit exactly as `slf profile build` does."""
    wide = pf.census_wide(observations)
    universe = sorted(geographies.loc[geographies["level"] == 3, "geography_id"].astype(str))
    blocks = pf.BLOCKS_BY_LEVEL["ds"]
    x, _excluded = pf.prepare(wide, universe, blocks)
    return pf.fit(x, blocks)


def profile_vectors(profile_dir: Path) -> pd.DataFrame:
    vectors = sorted(
        p
        for p in (profile_dir / "vectors").glob("profile_v*.parquet")
        if not p.stem.endswith("_axes")
    )[-1]
    frame = pd.read_parquet(vectors)
    return pd.DataFrame(frame[(frame["level"] == "ds") & (frame["entity_type"] == "place")])


def check_refit(f: pf.Fit, profile_dir: Path) -> float:
    """Largest difference between the rebuilt scores and the stored profile vectors.

    The profile build stores vectors as float32, so differences up to about 1e-6 are storage
    precision, not a different fit.
    """
    stored = profile_vectors(profile_dir).set_index("entity_id")
    if sorted(stored.index) != sorted(f.ids):
        raise ValueError("rebuilt DS profile has different places from the stored profile build")
    scores = f.scores
    return float(
        max(
            np.abs(np.asarray(stored.loc[gid, "vector"], dtype=float) - scores[i]).max()
            for i, gid in enumerate(f.ids)
        )
    )


# --- typology ------------------------------------------------------------------------------


def kmeans(
    x: np.ndarray, k: int, rng: np.random.Generator, restarts: int = RESTARTS, iters: int = 300
) -> tuple[np.ndarray, np.ndarray, float]:
    """Lloyd's k-means with k-means++ starts; the best of ``restarts`` runs by inertia."""
    best: tuple[np.ndarray, np.ndarray, float] | None = None
    n = len(x)
    for _ in range(restarts):
        centres = [x[rng.integers(n)]]
        for _ in range(1, k):
            d2 = np.min(((x[:, None, :] - np.asarray(centres)[None]) ** 2).sum(-1), axis=1)
            total = d2.sum()
            pick = rng.choice(n, p=d2 / total) if total > 0 else rng.integers(n)
            centres.append(x[pick])
        c = np.asarray(centres, dtype=float)
        labels = np.zeros(n, dtype=int)
        for step in range(iters):
            d = ((x[:, None, :] - c[None]) ** 2).sum(-1)
            new = d.argmin(axis=1)
            if step and np.array_equal(new, labels):
                break
            labels = new
            for j in range(k):
                members = x[labels == j]
                c[j] = members.mean(axis=0) if len(members) else x[rng.integers(n)]
        inertia = float(((x - c[labels]) ** 2).sum())
        if best is None or inertia < best[2]:
            best = (labels.copy(), c.copy(), inertia)
    assert best is not None
    return best


def silhouette(x: np.ndarray, labels: np.ndarray) -> float:
    d = np.sqrt(((x[:, None, :] - x[None]) ** 2).sum(-1))
    out = np.zeros(len(x))
    for i in range(len(x)):
        own = labels == labels[i]
        if own.sum() <= 1:
            continue
        a = d[i, own].sum() / (own.sum() - 1)
        b = min(d[i, labels == j].mean() for j in set(labels.tolist()) if j != labels[i])
        out[i] = (b - a) / max(a, b)
    return float(out.mean())


def adjusted_rand(a: np.ndarray, b: np.ndarray) -> float:
    """Adjusted Rand index of two partitions of the same items (1 = identical)."""
    table = pd.crosstab(a, b).to_numpy()
    comb = lambda v: v * (v - 1) / 2  # noqa: E731
    index = comb(table).sum()
    rows, cols = comb(table.sum(axis=1)).sum(), comb(table.sum(axis=0)).sum()
    expected = rows * cols / comb(table.sum())
    top = (rows + cols) / 2
    return float((index - expected) / (top - expected)) if top != expected else 1.0


def bootstrap(
    x: np.ndarray, k: int, labels: np.ndarray, rng: np.random.Generator, runs: int
) -> tuple[float, np.ndarray]:
    """Mean ARI of bootstrap partitions vs ``labels``, and each place's co-membership agreement.

    Each run fits k-means on a resample, assigns every place to its nearest centre, and compares
    with the full-data partition. A place's agreement is the mean Jaccard overlap between its
    full-data type mates and its mates in each run.
    """
    aris, agree = [], np.zeros(len(x))
    for _ in range(runs):
        sample = x[rng.integers(len(x), size=len(x))]
        _, centres, _ = kmeans(sample, k, rng, restarts=5)
        run = ((x[:, None, :] - centres[None]) ** 2).sum(-1).argmin(axis=1)
        aris.append(adjusted_rand(labels, run))
        for i in range(len(x)):
            ref, now = labels == labels[i], run == run[i]
            agree[i] += (ref & now).sum() / (ref | now).sum()
    return float(np.mean(aris)), agree / runs


def type_name(centre: np.ndarray, f: pf.Fit) -> tuple[str, list[list[Any]]]:
    """Draft name from the centre's inputs, back-projected from the retained axes (SD units)."""
    if f.weights is None:
        raise ValueError("fit has no weights")
    sd_units = (centre @ f.basis.T) / f.weights
    order = np.argsort(-sd_units)
    above = [j for j in order if sd_units[j] >= NAME_MIN_SD][:2]
    below = [j for j in order[::-1] if sd_units[j] <= -NAME_MIN_SD][:2]

    def label(j: int) -> str:
        return pf.INPUT_LABELS.get(f.columns[j], f.columns[j])

    parts = []
    if above:
        parts.append("higher " + " and ".join(label(j) for j in above))
    if below:
        parts.append("lower " + " and ".join(label(j) for j in below))
    name = "; ".join(parts) if parts else "close to the national average"
    profile_rows = [[f.columns[j], round(float(sd_units[j]), 3)] for j in order]
    return name[0].upper() + name[1:], profile_rows


def build_typology(f: pf.Fit, out_dir: Path, runs: int = BOOTSTRAP_RUNS) -> dict[str, Any]:
    x = f.scores
    rng = np.random.default_rng(SEED)
    choices = []
    fits: dict[int, tuple[np.ndarray, np.ndarray, float]] = {}
    for k in K_RANGE:
        fits[k] = kmeans(x, k, rng)
        stab, _ = bootstrap(x, k, fits[k][0], rng, runs)
        choices.append(
            {
                "k": k,
                "silhouette": round(silhouette(x, fits[k][0]), 4),
                "stability_ari": round(stab, 4),
                "inertia": round(fits[k][2], 4),
            }
        )
    stable = [c for c in choices if c["stability_ari"] >= MIN_STABILITY]
    pick = (
        max(stable, key=lambda c: (c["silhouette"], -c["k"]))
        if stable
        else max(choices, key=lambda c: c["stability_ari"])
    )
    k = int(pick["k"])
    labels, centres, _ = fits[k]
    _, agreement = bootstrap(x, k, labels, np.random.default_rng(SEED + k), runs)
    # Types are numbered by size (largest first), a neutral order.
    sizes = Counter(labels.tolist())
    order = sorted(range(k), key=lambda j: (-sizes[j], j))
    renumber = {old: new for new, old in enumerate(order)}
    labels = np.array([renumber[j] for j in labels])
    centres = centres[order]
    dist = np.sqrt(((x - centres[labels]) ** 2).sum(-1))
    types = []
    for j in range(k):
        members = np.where(labels == j)[0]
        name, inputs = type_name(centres[j], f)
        typical = members[np.argsort(dist[members])][:3]
        types.append(
            {
                "type": j + 1,
                "draft_name": name,
                "label_status": LABEL_STATUS,
                "size": len(members),
                "centre": [round(float(v), DECIMALS) for v in centres[j]],
                "inputs_sd": inputs[:6] + inputs[-6:],
                "typical": [f.ids[i] for i in typical],
                "mean_agreement": round(float(agreement[members].mean()), 4),
            }
        )
    places = pd.DataFrame(
        {
            "geography_id": f.ids,
            "space_id": TYPOLOGY_ID,
            "space_version": TYPOLOGY_VERSION,
            "type": labels + 1,
            "distance_to_centre": dist.round(DECIMALS),
            "agreement": agreement.round(4),
        }
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    places.to_parquet(out_dir / f"typology_ds_v{TYPOLOGY_VERSION}.parquet", index=False)
    payload = {
        "space_id": TYPOLOGY_ID,
        "space_version": TYPOLOGY_VERSION,
        "base": {"space_id": pf.SPACE_ID, "space_version": pf.SPACE_VERSION, "level": "ds"},
        "method": (
            f"k-means (k-means++ starts, best of {RESTARTS}) on the DS profile vectors; k chosen "
            f"from {K_RANGE.start}-{K_RANGE.stop - 1} as the highest silhouette among k whose mean "
            f"bootstrap adjusted Rand index over {runs} resamples is at least {MIN_STABILITY}."
        ),
        "note": (
            "Types group DS divisions that are close in the profile space. A type is a "
            "similarity grouping, not a fact about a place, and not a ranking. Names are machine "
            "drafts from each type's average inputs and await review."
        ),
        "k": k,
        "choices": choices,
        "types": types,
        "ids": f.ids,
        "type_of": [int(v) for v in labels + 1],
        "agreement": [round(float(v), 4) for v in agreement],
    }
    _dump(out_dir / "typology.json", payload)
    return {
        "k": k,
        "choices": choices,
        "sizes": [t["size"] for t in types],
        "min_type_agreement": min(t["mean_agreement"] for t in types),
        "places": len(f.ids),
    }


# --- trajectory (private, D-038) -------------------------------------------------------------


def build_trajectory(history_dir: Path, wide: pd.DataFrame, out_dir: Path) -> dict[str, Any]:
    comparison = pd.read_csv(
        history_dir / "ds_comparison_2012_2024.csv", dtype={"geography_id": str}
    )
    units = pd.read_csv(history_dir / "ds_2012_units.csv", dtype=str)
    comparison = comparison[comparison["geography_id"].notna()]
    predecessors: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in units.to_dict("records"):
        if isinstance(row.get("geography_id"), str):
            predecessors[row["geography_id"]].append(row)
    rows, excluded = [], []
    for row in pd.DataFrame(comparison).to_dict("records"):
        gid = str(row["geography_id"])
        preds = predecessors.get(gid, [])
        growth = row["annual_rate_pct"]
        if pd.isna(growth):
            excluded.append({"id": gid, "reason": "no population comparison"})
            continue
        if len(preds) != 1 or preds[0]["change_type"] not in ("unchanged", "renamed"):
            excluded.append(
                {
                    "id": gid,
                    "reason": "no one-to-one 2012 predecessor (split or boundary change), so the "
                    "2012 sex ratio is not on the same footprint",
                }
            )
            continue
        male, female = float(preds[0]["male"]), float(preds[0]["female"])
        sr24 = wide.at[gid, "sex_ratio"] if gid in wide.index else float("nan")
        if female <= 0 or pd.isna(sr24):
            excluded.append({"id": gid, "reason": "sex ratio undefined in one census"})
            continue
        rows.append(
            {
                "id": gid,
                "growth": float(growth),
                "sex_ratio_change": round(float(sr24) - 100.0 * male / female, 4),
                "comparison": str(row["comparison"]),
            }
        )
    frame = pd.DataFrame(rows).sort_values("id").reset_index(drop=True)
    raw = frame[["growth", "sex_ratio_change"]].to_numpy(float)
    mean, sd = raw.mean(axis=0), raw.std(axis=0)
    z = np.round((raw - mean) / sd, DECIMALS)
    ids = frame["id"].tolist()
    similar = nearest_rows(z, ids, TRAJECTORY_K)
    axes = [
        {
            "id": "growth",
            "label": "annual population growth, 2012-2024 (%)",
            "mean": round(float(mean[0]), 4),
            "sd": round(float(sd[0]), 4),
        },
        {
            "id": "sex_ratio_change",
            "label": "change in males per 100 females, 2012-2024",
            "mean": round(float(mean[1]), 4),
            "sd": round(float(sd[1]), 4),
        },
    ]
    payload = {
        "space_id": TRAJECTORY_ID,
        "space_version": TRAJECTORY_VERSION,
        "status": "local_build_not_in_release",
        "note": (
            "Change between the 2012 and 2024 censuses. Private under D-038: built from the "
            "local history build, not in any release, not for publication. Each axis is "
            "standardised (mean 0, SD 1 across the units in the space); distance is Euclidean, "
            "and each axis's share of a squared distance is exact."
        ),
        "axes": axes,
        "ids": ids,
        "vectors": z.tolist(),
        "raw": [[round(float(a), 4), round(float(b), 4)] for a, b in raw],
        "comparison": frame["comparison"].tolist(),
        "excluded": excluded,
        "similar": similar,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    _dump(out_dir / "trajectory.json", payload)
    return {
        "places": len(ids),
        "excluded": len(excluded),
        "approximate_in_space": int((frame["comparison"] == "approximate").to_numpy().sum()),
    }


def nearest_rows(z: np.ndarray, ids: Sequence[str], k: int) -> dict[str, list[list[float | str]]]:
    """k nearest by Euclidean distance; ties broken by id, as the browser does."""
    out: dict[str, list[list[float | str]]] = {}
    d = np.sqrt(((z[:, None, :] - z[None]) ** 2).sum(-1))
    for i, gid in enumerate(ids):
        order = sorted((j for j in range(len(ids)) if j != i), key=lambda j: (d[i, j], ids[j]))
        out[gid] = [[ids[j], round(float(d[i, j]), DECIMALS)] for j in order[:k]]
    return out


# --- composite -------------------------------------------------------------------------------


def block_contributions(f: pf.Fit) -> tuple[list[str], np.ndarray]:
    """Per place, block and axis: that block's part of the axis score (sums to the score)."""
    blocks = pf.BLOCKS_BY_LEVEL["ds"]
    names = list(blocks)
    basis = f.basis
    contrib = np.zeros((len(f.ids), len(names), basis.shape[1]))
    for b, name in enumerate(names):
        cols = [f.columns.index(c) for c in blocks[name]]
        contrib[:, b, :] = f.z[:, cols] @ basis[cols, :]
    return names, contrib


def composite_scores(contrib: np.ndarray, weights: Sequence[float]) -> np.ndarray:
    return np.einsum("iba,b->ia", contrib, np.asarray(weights, dtype=float))


def build_composite(f: pf.Fit, out_dir: Path) -> dict[str, Any]:
    names, contrib = block_contributions(f)
    rebuilt_error = float(np.abs(contrib.sum(axis=1) - f.scores).max())
    contrib = np.round(contrib, DECIMALS)
    axes = [
        {"axis": int(j) + 1, "draft_label": pf.axis_label(f, int(j)), "label_status": LABEL_STATUS}
        for j in f.retained
    ]
    payload = {
        "space_id": COMPOSITE_ID,
        "space_version": COMPOSITE_VERSION,
        "base": {"space_id": pf.SPACE_ID, "space_version": pf.SPACE_VERSION, "level": "ds"},
        "note": (
            "The profile space with a weight per block. Each axis score is the sum of its block "
            "contributions; a weight scales one block's contributions. All weights 1 gives "
            "profile v0.3 exactly. Distances use all retained axes, never screen positions."
        ),
        "blocks": [
            {"id": n, "label": BLOCK_LABELS.get(n, n), "inputs": len(pf.BLOCKS_BY_LEVEL["ds"][n])}
            for n in names
        ],
        "axes": axes,
        "ids": f.ids,
        "contrib": contrib.tolist(),
    }
    expected = {
        name: {
            "weights": [weights[n] for n in names],
            "similar": nearest_rows(
                composite_scores(contrib, [weights[n] for n in names]), f.ids, COMPOSITE_K
            ),
        }
        for name, weights in COMPOSITE_PRESETS.items()
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    _dump(out_dir / "composite.json", payload)
    _dump(out_dir / "expected_composite.json", expected)
    return {"places": len(f.ids), "blocks": names, "block_sum_error": rebuilt_error}


# --- text ------------------------------------------------------------------------------------

_INDIC = re.compile("[඀-෿஀-௿]")
_SPACE = re.compile("[\t\n\r\f\v \u00a0]+")


def normalise(value: str) -> str:
    """Fold a name exactly as `web/src/lib/search.ts` `normalise` does."""
    text = unicodedata.normalize("NFC", value).lower().strip()
    if _INDIC.search(text):
        return _SPACE.sub(" ", text).strip()
    folded = "".join(ch for ch in unicodedata.normalize("NFD", text) if not ("̀" <= ch <= "ͯ"))
    folded = re.sub(r"[^a-z0-9 ]+", " ", folded)
    folded = _SPACE.sub(" ", folded)
    for a, b in (("oo", "u"), ("ou", "u"), ("th", "t"), ("ph", "f"), ("dh", "d"), ("bh", "b")):
        folded = folded.replace(a, b)
    folded = folded.replace("gh", "g").replace("w", "v")
    folded = re.sub(r"(.)\1+", r"\1", folded)
    return folded.strip()


def grams(text: str) -> Counter[str]:
    padded = f" {text} "
    chars = list(padded)
    out: Counter[str] = Counter()
    for n in (2, 3):
        for i in range(len(chars) - n + 1):
            out["".join(chars[i : i + n])] += 1
    return out


@dataclass
class TextIndex:
    place_of: list[int]  # document -> place row
    ids: list[str]
    levels: list[int]
    names: list[str]
    idf: dict[str, float]
    postings: dict[str, tuple[np.ndarray, np.ndarray]]  # gram -> (documents, unit weights)
    n_docs: int


def text_documents(entries: Iterable[dict[str, Any]]) -> list[tuple[str, int, str, str]]:
    """(place id, level, English name, normalised name) for every non-empty name of a place."""
    docs = []
    for e in entries:
        en = e.get("name_en") or e.get("name_si") or e.get("name_ta") or e["geography_id"]
        for name in (en, e.get("name_si"), e.get("name_ta")):
            if name:
                folded = normalise(str(name))
                if folded:
                    docs.append((str(e["geography_id"]), int(e["level"]), str(en), folded))
    return docs


def build_text_index(entries: Iterable[dict[str, Any]]) -> TextIndex:
    docs = text_documents(entries)
    ids, levels, names, place_of = [], [], [], []
    row: dict[str, int] = {}
    for gid, level, en, _ in docs:
        if gid not in row:
            row[gid] = len(ids)
            ids.append(gid)
            levels.append(level)
            names.append(en)
        place_of.append(row[gid])
    counts = [grams(d[3]) for d in docs]
    df: Counter[str] = Counter()
    for c in counts:
        df.update(c.keys())
    n = len(docs)
    idf = {g: math.log((n + 1) / (v + 1)) + 1.0 for g, v in df.items()}
    lists: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for d, c in enumerate(counts):
        weights = {g: tf * idf[g] for g, tf in c.items()}
        norm = math.sqrt(sum(w * w for w in weights.values()))
        for g, w in weights.items():
            lists[g].append((d, w / norm))
    postings = {
        g: (np.array([d for d, _ in v], dtype=np.int64), np.array([w for _, w in v]))
        for g, v in lists.items()
    }
    return TextIndex(place_of, ids, levels, names, idf, postings, n)


def text_search(index: TextIndex, query: str, k: int = TEXT_K) -> list[tuple[str, float]]:
    """Places by best cosine over their names; ties by level (coarser first), then id."""
    folded = normalise(query)
    if not folded:
        return []
    q = grams(folded)
    unseen = math.log(index.n_docs + 1) + 1.0
    weights = {g: tf * index.idf.get(g, unseen) for g, tf in q.items()}
    norm = math.sqrt(sum(w * w for w in weights.values()))
    scores = np.zeros(index.n_docs)
    for g, w in weights.items():
        if g in index.postings:
            docs, vals = index.postings[g]
            np.add.at(scores, docs, vals * (w / norm))
    best: dict[int, float] = {}
    for d in np.nonzero(scores > 0)[0]:
        p = index.place_of[int(d)]
        if scores[d] > best.get(p, 0.0):
            best[p] = float(scores[d])
    order = sorted(best, key=lambda p: (-round(best[p], 9), index.levels[p], index.ids[p]))
    return [(index.ids[p], round(best[p], DECIMALS)) for p in order[:k]]


def typo(text: str) -> str:
    """Drop the middle character: a deterministic misspelling for the agreement check."""
    chars = list(text)
    if len(chars) < 4:
        return text
    del chars[len(chars) // 2]
    return "".join(chars)


def build_text(admin: list[dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    index = build_text_index(admin)
    queries: list[str] = []
    seen: set[str] = set()
    for e in admin:
        for name in (e.get("name_en"), e.get("name_si"), e.get("name_ta")):
            if name:
                q = typo(str(name))
                if q not in seen:
                    seen.add(q)
                    queries.append(q)
    expected = {q: text_search(index, q) for q in queries}
    self_hits = sum(
        1
        for e in admin
        if e.get("name_en")
        and any(gid == e["geography_id"] for gid, _ in text_search(index, str(e["name_en"]), 1))
    )
    meta = {
        "space_id": TEXT_ID,
        "space_version": TEXT_VERSION,
        "method": (
            "Names folded as the website's search does (romanisation variants; Sinhala and Tamil "
            "kept as written), padded with a space, split into character 2- and 3-grams; weight "
            "= count x idf, idf = ln((N+1)/(df+1)) + 1 over all name documents; cosine "
            "similarity; a place scores its best name."
        ),
        "documents": index.n_docs,
        "places": len(index.ids),
        "grams": len(index.idf),
        "aliases": "none held (alt_names empty in the spine)",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    _dump(out_dir / "text.json", meta)
    _dump(out_dir / "expected_text.json", {"k": TEXT_K, "queries": expected})
    return {**meta, "queries_checked": len(queries), "exact_name_top1": self_hits}


# --- one command -----------------------------------------------------------------------------


def build_all(
    observations: pd.DataFrame,
    geographies: pd.DataFrame,
    profile_dir: Path,
    history_dir: Path | None,
    admin: list[dict[str, Any]],
    out_dir: Path,
    runs: int = BOOTSTRAP_RUNS,
) -> dict[str, Any]:
    f = refit_ds(observations, geographies)
    summary: dict[str, Any] = {"refit_max_difference": check_refit(f, profile_dir)}
    summary["typology"] = build_typology(f, out_dir, runs)
    summary["composite"] = build_composite(f, out_dir)
    summary["trajectory"] = (
        build_trajectory(history_dir, pf.census_wide(observations), out_dir)
        if history_dir is not None and (history_dir / "ds_comparison_2012_2024.csv").exists()
        else {"available": False, "reason": "no history build"}
    )
    summary["text"] = build_text(admin, out_dir)
    _dump(out_dir / "summary.json", summary)
    return summary
