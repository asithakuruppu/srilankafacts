"""Registry of dataset modules, by dataset id."""

from slf.dataset import Dataset
from slf.datasets.census_2024_gnd import Census2024Gnd
from slf.datasets.example_dataset import ExampleDataset

REGISTRY: dict[str, type[Dataset]] = {
    Census2024Gnd.dataset_id: Census2024Gnd,
    ExampleDataset.dataset_id: ExampleDataset,
}
