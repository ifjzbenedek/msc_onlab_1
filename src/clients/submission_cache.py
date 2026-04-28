import hashlib
import os
import sqlite3
import time
from typing import Optional

from src.models.result import SubmissionResult


class SubmissionCache:

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

        folder = os.path.dirname(db_path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                slug TEXT NOT NULL,
                lang TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                submission_id INTEGER,
                accepted INTEGER NOT NULL,
                status TEXT NOT NULL,
                total_correct INTEGER,
                total_testcases INTEGER,
                runtime_percentile REAL,
                memory_percentile REAL,
                compile_error TEXT,
                runtime_error TEXT,
                last_testcase TEXT,
                code_output TEXT,
                expected_output TEXT,
                submitted_at REAL NOT NULL,
                PRIMARY KEY (slug, lang, code_hash)
            )
        """)
        conn.commit()
        conn.close()

    def get(self, slug: str, lang: str, code: str) -> Optional[SubmissionResult]:
        h = hashlib.sha256(code.encode()).hexdigest()

        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT submission_id, accepted, status, total_correct, total_testcases, "
            "runtime_percentile, memory_percentile, compile_error, runtime_error, "
            "last_testcase, code_output, expected_output "
            "FROM submissions WHERE slug=? AND lang=? AND code_hash=?",
            (slug, lang, h),
        ).fetchone()
        conn.close()

        if row is None:
            return None

        return SubmissionResult(
            slug=slug,
            submission_id=row[0] or 0,
            accepted=bool(row[1]),
            status=row[2],
            total_correct=row[3],
            total_testcases=row[4],
            runtime_percentile=row[5],
            memory_percentile=row[6],
            compile_error=row[7],
            runtime_error=row[8],
            last_testcase=row[9],
            code_output=row[10],
            expected_output=row[11],
        )

    def put(self, slug: str, lang: str, code: str, result: SubmissionResult) -> None:
        h = hashlib.sha256(code.encode()).hexdigest()

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO submissions VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                slug, lang, h,
                result.submission_id,
                int(result.accepted),
                result.status,
                result.total_correct,
                result.total_testcases,
                result.runtime_percentile,
                result.memory_percentile,
                result.compile_error,
                result.runtime_error,
                result.last_testcase,
                result.code_output,
                result.expected_output,
                time.time(),
            ),
        )
        conn.commit()
        conn.close()
