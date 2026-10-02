"""Optional bounded playback measurements; no disk I/O while sending inputs."""
from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path


class PlaybackTrace:
    def __init__(self, limit: int = 50000):
        self.limit = max(0, limit)
        self.records: list[dict] = []
        self.counts: Counter = Counter()
        self.dropped_records = 0
        self.started = time.perf_counter()
        self.cycle = 1

    def record(self, record: dict) -> None:
        item = dict(record)
        item.setdefault("elapsed_seconds", time.perf_counter() - self.started)
        self.cycle = item.get("cycle", self.cycle)
        item.setdefault("cycle", self.cycle)
        self.counts[item["type"]] += 1
        if item["type"] == "input_sent":
            self.counts[item["kind"]] += 1
        if len(self.records) < self.limit:
            self.records.append(item)
        else:
            self.dropped_records += 1

    def save(self, folder: Path, version: str, options, metadata: dict,
             outcome: str, error: str | None = None) -> Path:
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"playback-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:12]}.json"
        settings = asdict(options)
        settings["mode"] = options.mode.value
        data = {
            "schema_version": 1, "app_version": version,
            "measurement": "input_sent_only", "site_actions_confirmed": None,
            "settings": settings, "metadata": metadata, "outcome": outcome,
            "error": error, "counts": dict(self.counts),
            "dropped_records": self.dropped_records, "records": self.records,
        }
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=folder,
                                             delete=False, suffix=".tmp") as stream:
                temporary = Path(stream.name)
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return target
