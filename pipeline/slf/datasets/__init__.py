"""Registry of dataset modules, by dataset id."""

from slf.dataset import Dataset
from slf.datasets.example_dataset import ExampleDataset

REGISTRY: dict[str, type[Dataset]] = {
    ExampleDataset.dataset_id: ExampleDataset,
}
