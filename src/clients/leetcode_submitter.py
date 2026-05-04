import logging
import time
from typing import Optional

import httpx

from src.clients.rate_limiter import RateLimiter
from src.clients.submission_cache import SubmissionCache
from src.models.result import SubmissionResult
from src.utils.exceptions import RateLimitedError

log = logging.getLogger(__name__)


_SUBMISSION_DETAILS_QUERY = """
query submissionDetails($submissionId: Int!) {
    submissionDetails(submissionId: $submissionId) {
        statusCode
        runtimePercentile
        memoryPercentile
        totalCorrect
        totalTestcases
        compileError
        runtimeError
        lastTestcase
        codeOutput
        expectedOutput
    }
}
"""


STATUS_CODES = {
    10: "Accepted",
    11: "Wrong Answer",
    12: "Memory Limit Exceeded",
    13: "Output Limit Exceeded",
    14: "Time Limit Exceeded",
    15: "Runtime Error",
    16: "Internal Error",
    20: "Compile Error",
}


class LeetCodeSubmitter:

    def __init__(self, session_cookie: str,
                 graphql_url: str = "https://leetcode.com/graphql",
                 cache: Optional[SubmissionCache] = None,
                 rate_limiter: Optional[RateLimiter] = None) -> None:
        self._graphql_url = graphql_url
        self.cache = cache
        self.rate_limiter = rate_limiter

        self._http = httpx.Client(
            cookies={"LEETCODE_SESSION": session_cookie},
            headers={
                "Referer": "https://leetcode.com",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Origin": "https://leetcode.com",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        self._refresh_csrf()

    def _refresh_csrf(self) -> None:
        if "csrftoken" in self._http.cookies:
            self._http.headers["x-csrftoken"] = self._http.cookies["csrftoken"]
            return
        self._force_refresh_csrf()

    def _force_refresh_csrf(self) -> None:
        self._http.cookies.delete("csrftoken")

        try:
            self._http.post(self._graphql_url, json={"query": "{ __typename }"})
        except httpx.HTTPError:
            pass

        if "csrftoken" not in self._http.cookies:
            for url in ("https://leetcode.com/", self._graphql_url):
                try:
                    self._http.get(url)
                except httpx.HTTPError:
                    pass
                if "csrftoken" in self._http.cookies:
                    break

        if "csrftoken" not in self._http.cookies:
            raise RuntimeError("could not obtain csrftoken from leetcode — session may be expired")
        self._http.headers["x-csrftoken"] = self._http.cookies["csrftoken"]

    def submit(self, slug: str, question_id: str, code: str, lang: str = "python3",
               max_retries: int = 4) -> SubmissionResult:

        if self.cache is not None:
            cached = self.cache.get(slug, lang, code)
            if cached is not None:
                log.info("cache hit for %s (%s) — %s", slug, lang, cached.status)
                return cached

        if self.rate_limiter is not None:
            self.rate_limiter.acquire()

        log.info("Submitting %s (%s)", slug, lang)
        self._refresh_csrf()

        resp = None
        for attempt in range(max_retries):
            resp = self._http.post(
                f"https://leetcode.com/problems/{slug}/submit/",
                json={
                    "question_id": question_id,
                    "lang": lang,
                    "typed_code": code,
                },
            )

            if resp.status_code == 200:
                break

            if resp.status_code in (429, 403) or 500 <= resp.status_code < 600:
                if attempt == max_retries - 1:
                    raise RateLimitedError(
                        f"got HTTP {resp.status_code} for {slug} after {max_retries} tries"
                    )
                wait = 60 * (2 ** attempt)
                log.warning("got HTTP %d, waiting %ds (attempt %d/%d)",
                            resp.status_code, wait, attempt + 1, max_retries)
                if resp.status_code == 403:
                    self._force_refresh_csrf()
                time.sleep(wait)
                continue

            resp.raise_for_status()

        submission_id = resp.json()["submission_id"]
        log.info("Submitted, id=%s — waiting for judge", submission_id)

        result = self._poll_result(slug, submission_id)

        if self.cache is not None:
            self.cache.put(slug, lang, code, result)

        return result

    def _poll_result(self, slug: str, submission_id: int, max_wait: int = 180) -> SubmissionResult:
        deadline = time.time() + max_wait
        time.sleep(10)

        while time.time() < deadline:
            resp = self._http.post(
                self._graphql_url,
                json={
                    "query": _SUBMISSION_DETAILS_QUERY,
                    "variables": {"submissionId": submission_id},
                },
            )
            resp.raise_for_status()
            details = resp.json()["data"]["submissionDetails"]

            if details is None:
                time.sleep(3)
                continue

            status_code = details["statusCode"]
            return SubmissionResult(
                slug=slug,
                submission_id=submission_id,
                accepted=status_code == 10,
                status=STATUS_CODES.get(status_code, f"Unknown ({status_code})"),
                total_correct=details["totalCorrect"],
                total_testcases=details["totalTestcases"],
                runtime_percentile=details["runtimePercentile"],
                memory_percentile=details["memoryPercentile"],
                compile_error=details["compileError"],
                runtime_error=details["runtimeError"],
                last_testcase=details["lastTestcase"],
                code_output=details["codeOutput"],
                expected_output=details["expectedOutput"],
            )

        raise TimeoutError(f"Judge did not finish within {max_wait}s for submission {submission_id}")
