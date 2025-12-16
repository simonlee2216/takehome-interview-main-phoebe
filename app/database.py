import json
import logging
from collections.abc import Callable, Iterator, MutableMapping
from pathlib import Path
from typing import TypeVar

K = TypeVar("K")
V = TypeVar("V")
logger = logging.getLogger(__name__)


class InMemoryKeyValueDatabase[K, V]:
    """
    Simple in-memory key/value database.
    """

    def __init__(self) -> None:
        self._store: MutableMapping[K, V] = {}

    def put(self, key: K, value: V) -> None:
        self._store[key] = value

    def get(self, key: K) -> V | None:
        return self._store.get(key)

    def delete(self, key: K) -> None:
        self._store.pop(key, None)

    def all(self) -> list[V]:
        return list(self._store.values())

    def clear(self) -> None:
        self._store.clear()

    # Universal search function
    def find(self, predicate: Callable[[V], bool]) -> list[V]:
        return [item for item in list(self._store.values()) if predicate(item)]

    def __iter__(self) -> Iterator[V]:
        return iter(self._store.values())

    def __len__(self) -> int:
        return len(self._store)


class Registry(InMemoryKeyValueDatabase[str, dict]):
    """
    Methods to avoid manual key formatting
    """

    # Shift helper funcs
    def get_shift(self, shift_id: str) -> dict | None:
        return self.get(f"shift:{shift_id}")

    def save_shift(self, shift: dict) -> None:
        self.put(f"shift:{shift['id']}", shift)

    # Caregiver helper funcs
    def get_caregiver(self, caregiver_id: str) -> dict | None:
        return self.get(f"caregiver:{caregiver_id}")

    def save_caregiver(self, caregiver: dict) -> None:
        self.put(f"caregiver:{caregiver['id']}", caregiver)

    def get_caregiver_phone(self, phone: str) -> dict | None:
        results = self.find(lambda x: x.get("phone") == phone)
        return results[0] if results else None

    def get_caregivers_role(self, role: str) -> list[dict]:
        return self.find(lambda x: x.get("role") == role)


db = Registry()


def load_data():
    """Loads sample data into database."""
    root = Path(__file__).parent.parent
    file = root / "sample_data.json"

    if not file.exists():
        logger.warning(f"Could not find {file}")
        return

    with open(file) as f:
        data = json.load(f)

    for shift in data.get("shifts", []):
        shift.update(
            {
                "status": "OPEN",
                "fanout_started": False,
                "assigned_caregiver_id": None,
            }
        )
        db.save_shift(shift)

    for caregiver in data.get("caregivers", []):
        db.save_caregiver(caregiver)

    logger.info(
        f"Loaded {len(data.get('shifts', []))} shifts and {len(data.get('caregivers', []))} caregivers."
    )
