"""Registry of dataset modules, by dataset id."""

from slf.dataset import Dataset
from slf.datasets.census_2024_gnd import Census2024Gnd
from slf.datasets.census_2024_topics import Census2024TopicTables
from slf.datasets.election_results import ElectionResults
from slf.datasets.example_dataset import ExampleDataset

REGISTRY: dict[str, type[Dataset]] = {
    Census2024Gnd.dataset_id: Census2024Gnd,
    Census2024TopicTables.dataset_id: Census2024TopicTables,
    ElectionResults.dataset_id: ElectionResults,
    ExampleDataset.dataset_id: ExampleDataset,
}
