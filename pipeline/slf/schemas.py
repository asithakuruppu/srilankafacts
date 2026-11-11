"""Catalogue and table schemas (prompt F02).

Field names and enums follow docs/architecture/data-model.md, spatial-first-analytics.md §3,
footprint-model.md §3 and vector-space-model.md §8. Each model is exported to JSON Schema in
catalog/schemas/ (`slf catalog schemas`) so editors and reviewers can read the rules.

Models forbid unknown keys: a typo in a YAML key is an error, not a silently ignored field.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Annotated, Literal, get_args

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9_-]*$")]
GeographyId = Annotated[str, StringConstraints(pattern=r"^LK[A-Za-z0-9-]*$")]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# --- Enums (data-model.md) -------------------------------------------------------------------

PublisherType = Literal[
    "government", "international", "academic", "civil_society", "commercial", "community"
]
AccessClass = Literal[
    "download_table", "pdf", "api", "web_query", "on_request", "licensed_microdata"
]
RightsStatus = Literal["open", "permitted_with_conditions", "unclear", "restricted"]
YesNoUnknown = Literal["yes", "no", "unknown"]
Schedule = Literal["manual", "daily", "weekly", "monthly", "on_release"]
CatalogStatus = Literal["proposed", "active", "paused", "retired"]
Support = Literal["area", "point", "line", "grid", "national"]
MeasureType = Literal["count", "share", "rate", "ratio", "currency", "index", "mean", "median"]
Aggregation = Literal["sum", "recompute_from_components", "none"]
HigherIs = Literal["better", "worse", "neutral"]
SupportType = Literal[
    "area_total", "area_mean", "location_uncertain", "object_extent", "field_sample"
]
TimeSupport = Literal["instant", "interval_total", "interval_mean", "snapshot", "observed_around"]
CollectionMethod = Literal[
    "enumeration",
    "admin_register",
    "sample_survey",
    "satellite_observation",
    "model",
    "crowd_mapped",
]
Sensitivity = Literal["public", "sensitive_group", "small_cell"]
RevisionStatus = Literal["provisional", "final", "revised"]
ValueStatus = Literal["normal", "not_available", "not_applicable", "suppressed", "provisional"]
DataNature = Literal[
    "census_count",
    "administrative_count",
    "survey_estimate",
    "official_estimate",
    "modelled_estimate",
    "reconstruction",
]
Verification = Literal[
    "machine_extracted", "spot_checked", "human_verified", "reconciled", "disputed"
]
MatchMethod = Literal["exact_code", "name_and_parent", "spatial", "manual"]
RelationType = Literal["parent", "composed_of", "succeeded_by", "preceded_by"]
RelationMethod = Literal[
    "attribute",
    "official_list",
    "overlay_buildings",
    "overlay_population",
    "overlay_area",
    "manual",
]
Nests = Literal["yes", "no", "partly", "unknown"]
Metric = Literal["euclidean", "cosine", "inner_product"]
EntityType = Literal["place", "indicator", "place_period", "feature", "cell"]

SUPPORT_TYPES: frozenset[str] = frozenset(get_args(SupportType))
TIME_SUPPORTS: frozenset[str] = frozenset(get_args(TimeSupport))

PERIOD_RE = re.compile(
    r"^\d{4}(-Q[1-4]|-(0[1-9]|1[0-2])(-(0[1-9]|[12]\d|3[01]))?|-W(0[1-9]|[1-4]\d|5[0-3]))?$"
    r"|^\d{4}/\d{2}-maha$|^\d{4}-yala$"
)


# --- Source ----------------------------------------------------------------------------------


class Rights(Strict):
    status: RightsStatus
    licence: str | None = None
    commercial_reuse: YesNoUnknown = "unknown"
    attribution: str | None = None
    evidence: list[str] = Field(default_factory=list)
    last_reviewed: dt.date

    @model_validator(mode="after")
    def _open_needs_evidence(self) -> Rights:
        if self.status in ("open", "permitted_with_conditions") and not self.evidence:
            raise ValueError(f"rights.status '{self.status}' needs at least one evidence entry")
        return self


class Source(Strict):
    id: Slug
    name: str
    publisher_type: PublisherType
    homepage: AnyHttpUrl | None = None
    contact: str | None = None
    access_classes: list[AccessClass] = Field(default_factory=list)
    rights: Rights
    notes: str | None = None


# --- Dataset ---------------------------------------------------------------------------------


class Spatial(Strict):
    """The spatial contract (spatial-first-analytics.md §3)."""

    support: Support
    scheme: str | None = None
    level: str | None = None
    vintage: str | None = None
    coverage: str | list[str] = "LK"
    measured_in: str | list[str] | None = None
    positional_accuracy: str | float | None = None
    crs_source: str | None = None
    resolution: str | None = None
    information_unit: str | None = None
    information_count: int | None = None
    derived_by: str | None = None

    @model_validator(mode="after")
    def _support_rules(self) -> Spatial:
        if self.support == "area" and not (self.scheme and self.level):
            raise ValueError("spatial.support 'area' needs scheme and level")
        if self.support == "grid" and not self.resolution:
            raise ValueError("spatial.support 'grid' needs resolution")
        if self.crs_source is not None and not re.match(
            r"^(EPSG:\d+|unconfirmed|not_applicable)$", self.crs_source
        ):
            raise ValueError(
                "spatial.crs_source must be 'EPSG:<code>', 'unconfirmed', 'not_applicable' or null"
            )
        return self


class CrossCheck(Strict):
    upstream: str
    note: str | None = None


class PublicationDecision(Strict):
    """A lead decision that allows publication while source rights are unclear (D-030).

    It is a recorded risk position, not a licence: `rights.status` stays `unclear`. Every release
    payload that carries the dataset's values then carries `use`, `attribution` and `notice`.
    """

    decision: Annotated[str, StringConstraints(pattern=r"^D-\d{3}$")]
    use: Literal["non_commercial"]
    attribution: str
    notice: str
    takedown_days: int = Field(gt=0)
    decided: dt.date


class Dataset(Strict):
    id: Slug
    source: Slug
    title: str
    landing_page: AnyHttpUrl | None = None
    pipeline_module: str | None = None
    schedule: Schedule = "manual"
    geography_scheme: str | None = None
    geography_vintage: str | None = None
    reference_period: str | None = None
    rights: Literal["inherit"] | Rights = "inherit"
    publication: PublicationDecision | None = None
    spatial: Spatial
    indicators: list[Slug] = Field(default_factory=list)
    cross_checks: list[CrossCheck] = Field(default_factory=list)
    status: CatalogStatus = "proposed"
    notes: str | None = None

    @field_validator("reference_period")
    @classmethod
    def _period(cls, v: str | None) -> str | None:
        if v is not None and not PERIOD_RE.match(v):
            raise ValueError(f"reference_period '{v}' is not a documented period format")
        return v


# --- Indicator -------------------------------------------------------------------------------


class Indicator(Strict):
    id: Slug
    name: str
    short_name: str | None = None
    topic: list[str] = Field(default_factory=list)
    measure_type: MeasureType
    unit: str
    universe: str | None = None
    numerator: Slug | None = None
    denominator: Slug | None = None
    aggregation: Aggregation
    higher_is: HigherIs = "neutral"
    decimals: int = Field(default=0, ge=0, le=6)
    sensitivity: Sensitivity = "public"
    definition: str
    source_definition_ref: str | None = None
    methodology_notes: str | None = None

    @model_validator(mode="after")
    def _components(self) -> Indicator:
        if self.aggregation == "recompute_from_components" and not (
            self.numerator and self.denominator
        ):
            raise ValueError(
                "aggregation 'recompute_from_components' needs numerator and denominator"
            )
        if self.measure_type == "count" and self.aggregation == "recompute_from_components":
            raise ValueError("a count is aggregated by 'sum', not recomputed")
        return self


# --- Geography schemes, codes, relations -----------------------------------------------------


class SchemeLevel(Strict):
    level: int = Field(ge=0)
    id: Slug
    name: str


class GeographyScheme(Strict):
    id: Slug
    name: str
    authority: str | None = None
    id_prefix: str | None = None
    levels: list[SchemeLevel]
    nests_in_admin: Nests | None = None
    derived: bool = False
    stage: str
    notes: str | None = None


class GeographySchemes(Strict):
    schemes: list[GeographyScheme]


class GeoCodeRow(Strict):
    """One row of catalog/geographies/codes/*.csv: an external code for one of our places."""

    geography_id: GeographyId
    vintage: str
    code_system: Slug
    external_code: str
    external_name: str | None = None
    match_method: MatchMethod
    confidence: float = Field(ge=0, le=1)
    notes: str | None = None


class GeoRelationRow(Strict):
    """One row of catalog/geographies/relations/*.csv: an edge in the place graph (D-021)."""

    geography_id: GeographyId
    related_id: GeographyId
    relation: RelationType
    vintage: str
    weight: float | None = Field(default=None, ge=0, le=1)
    method: RelationMethod
    source: str
    valid_from: dt.date | None = None
    valid_to: dt.date | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _weights(self) -> GeoRelationRow:
        if self.relation == "composed_of" and self.weight is None:
            raise ValueError("'composed_of' relations need a weight (0-1)")
        if self.geography_id == self.related_id:
            raise ValueError("a place cannot relate to itself")
        return self


class ProvisionalGeographyRow(Strict):
    """One row of catalog/geographies/provisional.csv: a unit missing from COD-AB (D-022).

    Provisional ids are never reused. The unit is defined by its `composed_of` relations to
    spine units (catalog/geographies/relations/provisional.csv); its geometry is derived.
    """

    geography_id: Annotated[str, StringConstraints(pattern=r"^LK-ADM[1-4]-P\d{4}$")]
    scheme: Literal["admin"]
    level: int = Field(ge=1, le=4)
    name_en: str
    name_si: str | None = None
    name_ta: str | None = None
    parent_id: GeographyId
    status: Literal["provisional", "retired"]
    valid_from: dt.date | None = None
    source: str
    evidence: str
    notes: str | None = None

    @model_validator(mode="after")
    def _level_in_id(self) -> ProvisionalGeographyRow:
        if self.geography_id[6] != str(self.level):
            raise ValueError("the level in the id (LK-ADM<level>-P…) must match `level`")
        return self


class ManualMatchRow(Strict):
    """One row of catalog/geographies/manual-matches.csv: a crosswalk decision made by a person.

    Applied after automatic matching and wins over it. `decision: review` forces an item into the
    review queue with the stated reason (for matches that look right but are not equivalent).
    """

    system: Slug
    level: int = Field(ge=1, le=4)
    code: str
    decision: Literal["match", "review", "no_counterpart"]
    geography_id: GeographyId | None = None
    evidence: str
    decided_by: str
    date: dt.date

    @model_validator(mode="after")
    def _target(self) -> ManualMatchRow:
        if (self.decision == "match") != (self.geography_id is not None):
            raise ValueError("geography_id is required for 'match' and must be empty otherwise")
        return self


class OverrideRow(Strict):
    """One row of overrides/*.csv: a human correction with evidence (AGENTS rule 3)."""

    override_id: Slug
    dataset_id: Slug
    target: str
    field: str
    old_value: str | None = None
    new_value: str | None = None
    reason: str
    evidence: str
    reviewer: str
    date: dt.date


# --- Vector spaces (vector-space-model.md §8) ------------------------------------------------


class SpaceInput(Strict):
    id: str
    kind: Literal["indicator", "geometry", "embedding", "derived"]
    weight: float = 1.0


class VectorSpace(Strict):
    id: Slug
    version: str
    title: str
    entity_types: list[EntityType]
    dimensions: int | None = Field(default=None, ge=1)
    metric: Metric
    inputs: list[SpaceInput]
    transformations: list[str] = Field(default_factory=list)
    excludes: list[str] = Field(default_factory=lambda: ["ethnicity", "religion"])
    status: CatalogStatus = "proposed"
    method_notes: str

    @model_validator(mode="after")
    def _sensitive(self) -> VectorSpace:
        bad = [i.id for i in self.inputs if any(w in i.id for w in ("ethnic", "religio"))]
        if bad:
            raise ValueError(
                f"inputs {bad} use ethnicity or religion; D-015 excludes them from default spaces"
            )
        return self


# --- Observation (data-model.md §5, footprint-model.md §3) -----------------------------------


class Observation(Strict):
    claim_id: str
    indicator_id: Slug
    geography_id: GeographyId | None = None
    geography_vintage: str
    period: str
    time_start: dt.date
    time_end: dt.date
    time_support: TimeSupport
    support_type: SupportType
    footprint_ref: str
    point: str | None = None
    uncertainty_m: float | None = Field(default=None, ge=0)
    information_footprint_ref: str | None = None
    universe: str | None = None
    collection_method: CollectionMethod | None = None
    sensitivity: Sensitivity = "public"
    revision_status: RevisionStatus | None = None
    origin_ref: str | None = None
    destination_ref: str | None = None
    preferred: bool = False
    preferred_reason: str | None = None
    breakdown: dict[str, str] | None = None
    value: float | None = None
    value_status: ValueStatus
    unit: str | None = None
    uncertainty_low: float | None = None
    uncertainty_high: float | None = None
    se: float | None = None
    data_nature: DataNature
    verification: Verification
    dataset_id: Slug
    snapshot_sha256: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
    source_locator: str
    override_id: str | None = None
    note_ids: list[str] = Field(default_factory=list)
    release: str | None = None

    @model_validator(mode="after")
    def _rules(self) -> Observation:
        if not PERIOD_RE.match(self.period):
            raise ValueError(f"period '{self.period}' is not a documented period format")
        if self.time_end < self.time_start:
            raise ValueError("time_end is before time_start")
        if self.value is None and self.value_status == "normal":
            raise ValueError("value is null but value_status is 'normal'")
        if self.preferred and not self.preferred_reason:
            raise ValueError("a preferred claim needs a preferred_reason")
        if self.support_type == "location_uncertain" and self.uncertainty_m is None:
            raise ValueError("support_type 'location_uncertain' needs uncertainty_m")
        if (self.origin_ref is None) != (self.destination_ref is None):
            raise ValueError("flows need both origin_ref and destination_ref")
        return self


EXPORTED_SCHEMAS: dict[str, type[BaseModel]] = {
    "source": Source,
    "dataset": Dataset,
    "indicator": Indicator,
    "geography-schemes": GeographySchemes,
    "geography-code-row": GeoCodeRow,
    "geography-relation-row": GeoRelationRow,
    "geography-provisional-row": ProvisionalGeographyRow,
    "geography-manual-match-row": ManualMatchRow,
    "override-row": OverrideRow,
    "vector-space": VectorSpace,
    "observation": Observation,
}
