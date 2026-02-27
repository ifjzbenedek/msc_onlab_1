import logging
import time

import httpx

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

# These are the status codes returned by LeetCode's submissionDetails API ( it's in a docs)
STATUS_CODES = {
    10: "Accepted",
    11: "Wrong Answer",
    14: "Time Limit Exceeded",
    15: "Runtime Error",
    20: "Compile Error",
}


class LeetCodeSubmitter:

    def __init__(self, session_cookie: str, graphql_url: str = "https://leetcode.com/graphql") -> None:
        self._graphql_url = graphql_url

        # Fetching csrftoken automatically
        self._http = httpx.Client(
            cookies={"LEETCODE_SESSION": session_cookie},
            headers={
                "Referer": "https://leetcode.com",
                "User-Agent": "Mozilla/5.0",
            },
            timeout=30,
        )
        csrf = self._fetch_csrf()
        self._http.headers["x-csrftoken"] = csrf
        self._http.cookies.set("csrftoken", csrf)

    def _fetch_csrf(self) -> str:
        # The html pages return 403, but the graphql endpoint sets the csrftoken cookie
        self._http.get(self._graphql_url)
        if "csrftoken" in self._http.cookies:
            return self._http.cookies["csrftoken"]
        raise RuntimeError("could not obtain csrftoken from leetcode")

    def submit(self, slug: str, question_id: str, code: str, lang: str = "python3") -> dict:
        log.info("Submitting %s (%s)", slug, lang)

        resp = self._http.post(
            f"https://leetcode.com/problems/{slug}/submit/",
            json={
                "question_id": question_id,
                "lang": lang,
                "typed_code": code,
            },
        )
        resp.raise_for_status()
        submission_id = resp.json()["submission_id"]
        log.info("Submitted, id=%s — waiting for judge", submission_id)

        return self._poll_result(submission_id)

    def _poll_result(self, submission_id: int, max_wait: int = 60) -> dict:
        deadline = time.time() + max_wait

        # Leetcode needs time to judge, which is 10s in the docs
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
                # Not ready yet
                time.sleep(3)
                continue

            status_code = details["statusCode"]
            return {
                "submission_id": submission_id,
                "status_code": status_code,
                "status": STATUS_CODES.get(status_code, f"Unknown ({status_code})"),
                "total_correct": details["totalCorrect"],
                "total_testcases": details["totalTestcases"],
                "runtime_percentile": details["runtimePercentile"],
                "memory_percentile": details["memoryPercentile"],
                "compile_error": details["compileError"],
                "runtime_error": details["runtimeError"],
                "last_testcase": details["lastTestcase"],
                "code_output": details["codeOutput"],
                "expected_output": details["expectedOutput"],
            }

        raise TimeoutError(f"Judge did not finish within {max_wait}s for submission {submission_id}")