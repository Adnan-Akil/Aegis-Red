"""
core_framework/storage/sqlite_manager.py

Async SQLite persistence layer using aiosqlite.
All framework data (targets, attempts, evaluations, findings) is stored here.

Usage:
    db = SQLiteManager("framework.db")
    await db.init()
    await db.save_attempt(attempt)
    attempts = await db.get_attempts_by_session("session-xyz")
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import aiosqlite

from .schemas import (
    AttackAttempt,
    EvaluationResult,
    TargetProfile,
    VulnerabilityFinding,
)

logger = logging.getLogger(__name__)

__all__ = ["SQLiteManager"]

DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "framework.db"


class SQLiteManager:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db: aiosqlite.Connection | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def init(self) -> None:
        """Open connection and create tables if they don't exist."""
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._create_tables()
        
        # Fast migration: add parent_payload_id if it doesn't exist
        try:
            await self._db.execute("ALTER TABLE attack_attempts ADD COLUMN parent_payload_id TEXT;")
        except aiosqlite.OperationalError:
            pass # Column likely exists already
            
        logger.debug("SQLite DB ready at %s", self.db_path)

        # Migrate any legacy hardened_* target rows to their base types
        await self._migrate_hardened_types()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    async def __aenter__(self) -> "SQLiteManager":
        await self.init()
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Migrations
    # ------------------------------------------------------------------

    async def _migrate_hardened_types(self) -> None:
        """One-shot migration: remap legacy hardened_* target_type rows to base types."""
        assert self._db is not None
        mapping = {
            "hardened_bot": "chatbot",
            "hardened_rag": "rag",
            "hardened_tool": "tool_agent",
        }
        for old_type, new_type in mapping.items():
            await self._db.execute(
                "UPDATE targets SET target_type = ? WHERE target_type = ?",
                (new_type, old_type),
            )
        await self._db.commit()
        logger.debug("Hardened-type migration complete.")

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    async def _create_tables(self) -> None:
        assert self._db is not None
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS targets (
                target_id   TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                url         TEXT NOT NULL,
                api_url     TEXT NOT NULL,
                target_type TEXT NOT NULL,
                port        INTEGER NOT NULL,
                metadata    TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS attack_attempts (
                attempt_id          TEXT PRIMARY KEY,
                session_id          TEXT NOT NULL,
                target_id           TEXT NOT NULL,
                payload_id          TEXT NOT NULL,
                category            TEXT NOT NULL,
                payload_text        TEXT NOT NULL,
                response_text       TEXT NOT NULL,
                tool_calls_triggered TEXT NOT NULL DEFAULT '[]',
                timestamp           TEXT NOT NULL,
                turn_index          INTEGER NOT NULL DEFAULT 0,
                duration_ms         INTEGER NOT NULL DEFAULT 0,
                parent_payload_id   TEXT
            );

            CREATE TABLE IF NOT EXISTS evaluation_results (
                attempt_id          TEXT PRIMARY KEY,
                verdict             TEXT NOT NULL,
                score               REAL NOT NULL,
                evaluation_method   TEXT NOT NULL,
                reasoning           TEXT NOT NULL,
                matched_indicators  TEXT NOT NULL DEFAULT '[]',
                timestamp           TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS vulnerability_findings (
                finding_id          TEXT PRIMARY KEY,
                session_id          TEXT NOT NULL,
                target_id           TEXT NOT NULL,
                category            TEXT NOT NULL,
                severity            TEXT NOT NULL,
                title               TEXT NOT NULL,
                description         TEXT NOT NULL,
                exploit_chain       TEXT NOT NULL DEFAULT '[]',
                reproduction_steps  TEXT NOT NULL DEFAULT '[]',
                confidence          REAL NOT NULL,
                discovered_at       TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_attempts_session
                ON attack_attempts(session_id);
            CREATE INDEX IF NOT EXISTS idx_findings_session
                ON vulnerability_findings(session_id);
        """)
        await self._db.commit()

    # ------------------------------------------------------------------
    # Targets
    # ------------------------------------------------------------------

    async def save_target(self, target: TargetProfile) -> None:
        assert self._db is not None
        meta = {
            "suspected_capabilities": target.suspected_capabilities,
            "known_constraints": target.known_constraints,
            "notes": target.notes,
        }
        await self._db.execute(
            """INSERT OR REPLACE INTO targets
               (target_id, name, url, api_url, target_type, port, metadata)
               VALUES (?,?,?,?,?,?,?)""",
            (target.target_id, target.name, target.url, target.api_url,
             target.target_type, target.port, json.dumps(meta)),
        )
        await self._db.commit()

    async def get_target(self, target_id: str) -> TargetProfile | None:
        assert self._db is not None
        async with self._db.execute(
            "SELECT * FROM targets WHERE target_id = ?", (target_id,)
        ) as cur:
            row = await cur.fetchone()
        if not row:
            return None
        meta = json.loads(row["metadata"])
        return TargetProfile(
            target_id=row["target_id"],
            name=row["name"],
            url=row["url"],
            api_url=row["api_url"],
            target_type=row["target_type"],
            port=row["port"],
            **meta,
        )

    # ------------------------------------------------------------------
    # Attack Attempts
    # ------------------------------------------------------------------

    async def save_attempt(self, attempt: AttackAttempt) -> None:
        assert self._db is not None
        await self._db.execute(
            """INSERT OR REPLACE INTO attack_attempts
               (attempt_id, session_id, target_id, payload_id, category,
                payload_text, response_text, tool_calls_triggered,
                timestamp, turn_index, duration_ms, parent_payload_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                attempt.attempt_id, attempt.session_id, attempt.target_id,
                attempt.payload_id, attempt.category, attempt.payload_text,
                attempt.response_text,
                json.dumps(attempt.tool_calls_triggered),
                attempt.timestamp.isoformat(), attempt.turn_index,
                attempt.duration_ms, attempt.parent_payload_id,
            ),
        )
        await self._db.commit()

    async def get_attempts_by_session(self, session_id: str) -> list[AttackAttempt]:
        assert self._db is not None
        rows = []
        async with self._db.execute(
            "SELECT * FROM attack_attempts WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        ) as cur:
            rows = await cur.fetchall()
        return [self._row_to_attempt(r) for r in rows]

    def _row_to_attempt(self, row: aiosqlite.Row) -> AttackAttempt:
        return AttackAttempt(
            attempt_id=row["attempt_id"],
            session_id=row["session_id"],
            target_id=row["target_id"],
            payload_id=row["payload_id"],
            category=row["category"],
            payload_text=row["payload_text"],
            response_text=row["response_text"],
            tool_calls_triggered=json.loads(row["tool_calls_triggered"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            turn_index=row["turn_index"],
            duration_ms=row["duration_ms"],
            parent_payload_id=row["parent_payload_id"] if "parent_payload_id" in row.keys() else None,
        )

    async def get_successful_mutations_by_type(
        self,
        target_type: str,
        target_id: str,
    ) -> list["AttackPayload"]:
        """
        Return memorized mutations that are likely to work against targets of
        *target_type*, ranked by cross-target reliability score.

        Rules:
        - Pulls from all targets whose type matches target_type
          (or ALL types when target_type == "unknown").
        - Computes reliability = success_count / total_attempts per payload.
        - Only includes payloads with reliability > 0.4.
        - Excludes any payload already attempted against *target_id* in any
          past session (no point repeating a known failure on the same bot).
        - Ordered by reliability descending so the best bets come first.
        """
        from src.memory.schemas import AttackPayload
        assert self._db is not None

        # For unknown targets we scatter-shot across all types
        type_filter = "" if target_type == "unknown" else "AND t.target_type = ?"
        params_base: tuple = () if target_type == "unknown" else (target_type,)

        query = f"""
            SELECT
                a.payload_id,
                a.category,
                a.payload_text,
                CAST(SUM(CASE WHEN e.verdict = 'success' THEN 1 ELSE 0 END) AS REAL)
                    / COUNT(*) AS reliability
            FROM attack_attempts a
            JOIN evaluation_results e ON a.attempt_id = e.attempt_id
            JOIN targets t            ON a.target_id  = t.target_id
            WHERE a.payload_id LIKE 'mut-%'
              {type_filter}
              AND a.payload_id NOT IN (
                  SELECT DISTINCT payload_id
                  FROM attack_attempts
                  WHERE target_id = ?
              )
            GROUP BY a.payload_id
            HAVING reliability > 0.4
            ORDER BY reliability DESC
        """

        rows = []
        async with self._db.execute(query, params_base + (target_id,)) as cur:
            rows = await cur.fetchall()

        payloads = []
        for r in rows:
            payloads.append(AttackPayload(
                payload_id=r["payload_id"],
                category=r["category"],
                name="memorized-mutation",
                template=r["payload_text"],
                tags=["memory"],
            ))
        return payloads

    # ------------------------------------------------------------------
    # Evaluation Results
    # ------------------------------------------------------------------

    async def save_evaluation(self, result: EvaluationResult) -> None:
        assert self._db is not None
        await self._db.execute(
            """INSERT OR REPLACE INTO evaluation_results
               (attempt_id, verdict, score, evaluation_method,
                reasoning, matched_indicators, timestamp)
               VALUES (?,?,?,?,?,?,?)""",
            (
                result.attempt_id, result.verdict, result.score,
                result.evaluation_method, result.reasoning,
                json.dumps(result.matched_indicators),
                result.timestamp.isoformat(),
            ),
        )
        await self._db.commit()

    async def get_evaluation(self, attempt_id: str) -> EvaluationResult | None:
        assert self._db is not None
        async with self._db.execute(
            "SELECT * FROM evaluation_results WHERE attempt_id = ?", (attempt_id,)
        ) as cur:
            row = await cur.fetchone()
        if not row:
            return None
        return EvaluationResult(
            attempt_id=row["attempt_id"],
            verdict=row["verdict"],
            score=row["score"],
            evaluation_method=row["evaluation_method"],
            reasoning=row["reasoning"],
            matched_indicators=json.loads(row["matched_indicators"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )

    # ------------------------------------------------------------------
    # Vulnerability Findings
    # ------------------------------------------------------------------

    async def save_finding(self, finding: VulnerabilityFinding) -> None:
        assert self._db is not None
        await self._db.execute(
            """INSERT OR REPLACE INTO vulnerability_findings
               (finding_id, session_id, target_id, category, severity,
                title, description, exploit_chain, reproduction_steps,
                confidence, discovered_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                finding.finding_id, finding.session_id, finding.target_id,
                finding.category, finding.severity, finding.title,
                finding.description,
                json.dumps(finding.exploit_chain),
                json.dumps(finding.reproduction_steps),
                finding.confidence,
                finding.discovered_at.isoformat(),
            ),
        )
        await self._db.commit()

    async def get_findings_by_session(
        self, session_id: str
    ) -> list[VulnerabilityFinding]:
        assert self._db is not None
        async with self._db.execute(
            "SELECT * FROM vulnerability_findings WHERE session_id = ? ORDER BY discovered_at",
            (session_id,),
        ) as cur:
            rows = await cur.fetchall()
        return [
            VulnerabilityFinding(
                finding_id=r["finding_id"],
                session_id=r["session_id"],
                target_id=r["target_id"],
                category=r["category"],
                severity=r["severity"],
                title=r["title"],
                description=r["description"],
                exploit_chain=json.loads(r["exploit_chain"]),
                reproduction_steps=json.loads(r["reproduction_steps"]),
                confidence=r["confidence"],
                discovered_at=datetime.fromisoformat(r["discovered_at"]),
            )
            for r in rows
        ]
