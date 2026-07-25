"""
src/memory/benchmark_store.py

Dual-layer Benchmark Persistence Manager.
Writes telemetry records to Supabase (production) or local SQLite (local CLI/dev).
Computes aggregate session summary metrics.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import aiosqlite

from src.memory.schemas import BenchmarkRecord

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "framework.db"


class BenchmarkStore:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def _init_local_db(self, db: aiosqlite.Connection) -> None:
        """Ensure benchmark_records table exists in SQLite."""
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS benchmark_records (
                record_id           TEXT PRIMARY KEY,
                session_id          TEXT NOT NULL,
                attack_id           TEXT NOT NULL,
                target_id           TEXT NOT NULL,
                target_type         TEXT NOT NULL,
                security_level      TEXT NOT NULL,
                attack_goal         TEXT NOT NULL,
                payload_category    TEXT NOT NULL,
                verdict             TEXT NOT NULL,
                score               REAL NOT NULL,
                pipeline_confidence REAL NOT NULL,
                component_scores    TEXT NOT NULL,
                evaluation_method   TEXT NOT NULL,
                is_community_shared INTEGER NOT NULL DEFAULT 1,
                timestamp           TEXT NOT NULL
            );
            """
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_br_session ON benchmark_records(session_id);"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_br_target ON benchmark_records(target_id);"
        )
        await db.commit()

    async def record(self, br: BenchmarkRecord, supabase_client: Any = None) -> None:
        """
        Record a benchmark entry.
        If Supabase manager is provided, syncs to Supabase.
        Always records to local SQLite as fallback/local store.
        """
        # 1. Local SQLite Write
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await self._init_local_db(db)
                await db.execute(
                    """
                    INSERT INTO benchmark_records (
                        record_id, session_id, attack_id, target_id, target_type,
                        security_level, attack_goal, payload_category, verdict,
                        score, pipeline_confidence, component_scores, evaluation_method,
                        is_community_shared, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        br.record_id,
                        br.session_id,
                        br.attack_id,
                        br.target_id,
                        br.target_type,
                        br.security_level,
                        br.attack_goal,
                        br.payload_category,
                        br.verdict,
                        br.score,
                        br.pipeline_confidence,
                        json.dumps(br.component_scores),
                        br.evaluation_method,
                        1 if br.is_community_shared else 0,
                        br.timestamp.isoformat(),
                    ),
                )
                await db.commit()
                logger.debug(f"[BenchmarkStore] Local SQLite record saved for attempt {br.attack_id}")
        except Exception as exc:
            logger.error(f"[BenchmarkStore] Failed writing local SQLite benchmark record: {exc}")

        # 2. Supabase Sync (if client available)
        if supabase_client and getattr(supabase_client, "supabase", None):
            try:
                data = {
                    "session_id": br.session_id,
                    "attack_id": br.attack_id,
                    "target_id": br.target_id,
                    "target_type": br.target_type,
                    "security_level": br.security_level,
                    "attack_goal": br.attack_goal,
                    "payload_category": br.payload_category,
                    "verdict": br.verdict,
                    "score": br.score,
                    "pipeline_confidence": br.pipeline_confidence,
                    "component_scores": br.component_scores,
                    "evaluation_method": br.evaluation_method,
                    "is_community_shared": br.is_community_shared,
                }
                supabase_client.supabase.table("benchmark_records").insert(data).execute()
                logger.info(f"[BenchmarkStore] Supabase synced benchmark record for attempt {br.attack_id}")
            except Exception as exc:
                logger.warning(f"[BenchmarkStore] Supabase benchmark_records sync failed (non-blocking): {exc}")

    async def get_session_summary(self, session_id: str) -> dict[str, Any]:
        """
        Calculates aggregate session metrics from stored benchmark records.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            await self._init_local_db(db)
            async with db.execute(
                "SELECT * FROM benchmark_records WHERE session_id = ? ORDER BY timestamp ASC;",
                (session_id,),
            ) as cursor:
                rows = await cursor.fetchall()

        if not rows:
            return {
                "session_id": session_id,
                "total_attempts": 0,
                "success_rate": 0.0,
                "per_category": {},
                "mean_pipeline_confidence": 0.0,
                "component_means": {},
            }

        total_attempts = len(rows)
        successes = sum(1 for r in rows if r["verdict"] == "success")
        success_rate = round(successes / total_attempts, 2) if total_attempts > 0 else 0.0

        mean_confidence = round(
            sum(r["pipeline_confidence"] for r in rows) / total_attempts, 2
        )

        # Per category metrics
        cat_counts: dict[str, int] = {}
        cat_successes: dict[str, int] = {}
        component_totals: dict[str, float] = {}
        component_counts: dict[str, int] = {}

        for r in rows:
            cat = r["payload_category"]
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            if r["verdict"] == "success":
                cat_successes[cat] = cat_successes.get(cat, 0) + 1

            comps: dict[str, float] = json.loads(r["component_scores"]) if isinstance(r["component_scores"], str) else r["component_scores"]
            for comp_name, comp_score in comps.items():
                component_totals[comp_name] = component_totals.get(comp_name, 0.0) + float(comp_score)
                component_counts[comp_name] = component_counts.get(comp_name, 0) + 1

        per_category = {
            cat: round(cat_successes.get(cat, 0) / count, 2)
            for cat, count in cat_counts.items()
        }

        component_means = {
            comp: round(component_totals[comp] / count, 2)
            for comp, count in component_counts.items()
        }

        return {
            "session_id": session_id,
            "total_attempts": total_attempts,
            "success_rate": success_rate,
            "per_category": per_category,
            "mean_pipeline_confidence": mean_confidence,
            "component_means": component_means,
        }
