import json
import os
from pathlib import Path
from datetime import datetime, date
from typing import Any
from enum import Enum

DB_DIR = Path("./data")
RESOURCE_PREFIXES = {
    "books": 196,
    "rooms": 297,
    "journals": 398,
    "archival": 499,
}


# extend json encoder to convert date and enum objects
class JSONEncoder(json.JSONEncoder):

    def default(self, o: Any) -> Any:

        # convert date os to ISO format
        if isinstance(o, (datetime, date)):
            return o.isoformat()

        # extract value attribute of enums
        if isinstance(o, Enum):
            return o.value

        return super().default(o)


def get_file_path(file_name: str):

    if file_name not in RESOURCE_PREFIXES:
        raise ValueError("Invalid file_name")

    return os.path.join(DB_DIR, f"{file_name}.json")


def _read_file(file_name: str):

    file_path = get_file_path(file_name)

    if not os.path.exists(file_path):
        return []

    with open(file_path, "r") as file:
        return json.load(file)


def _write_file(file_name: str, records: list):

    file_path = get_file_path(file_name)

    with open(file_path, "w") as file:
        json.dump(records, file, indent=4, cls=JSONEncoder)


def _generate_id(file_name: str, records: list):

    prefix = RESOURCE_PREFIXES[file_name]

    if not records:
        return prefix * 10000 + 1

    prev_id = max(int(record["id"]) for record in records)
    return prev_id + 1


def create(file_name: str, record: dict):

    records = _read_file(file_name)

    record["id"] = _generate_id(file_name, records)
    records.append(record)
    _write_file(file_name, records)

    return True


def update(file_name: str, record_id: int, new_record: dict):

    records = _read_file(file_name)

    for record in records:
        if record["id"] == record_id:
            record.update(new_record)
            _write_file(file_name, records)
            return record

    return None


def delete(file_name, record_id):

    records = _read_file(file_name)

    remaining = [record for record in records if record["id"] != record_id]
    if len(remaining) == len(records):
        return False

    _write_file(file_name, remaining)

    return True


def get_all_records(file_name: str):

    return _read_file(file_name)


def get_record(file_name: str, record_id: int):

    records = _read_file(file_name)

    for record in records:
        if record["id"] == record_id:
            return record

    return None
