import logging
import httpx
from src.models.problem import Problem

log = logging.getLogger(__name__)

# Fetch a single problem by slug
# All snippets are returned because the API can't filter by language, doing it later
_PROBLEM_QUERY = """
query getQuestionDetail($titleSlug: String!) {
    question(titleSlug: $titleSlug) {
        questionId
        title
        titleSlug
        difficulty
        content
        codeSnippets { langSlug code }
    }
}
"""
 
# Fetch the full problem list (slug, title, difficulty)
_PROBLEMSET_QUERY = """
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
    problemsetQuestionList: questionList(
        categorySlug: $categorySlug
        limit: $limit
        skip: $skip
        filters: $filters
    ) {
        total: totalNum
        questions: data {
            questionFrontendId
            title
            titleSlug
            difficulty
            isPaidOnly
        }
    }
}
"""


class LeetCodeClient:

    def __init__(self, graphql_url: str) -> None:
        self._url = graphql_url

    def fetch_problem(self, slug: str) -> Problem:

        raw = self._query(_PROBLEM_QUERY, {"titleSlug": slug})["question"]

        python3_stub = ""
        for snippet in raw["codeSnippets"]:
            if snippet["langSlug"] == "python3":
                python3_stub = snippet["code"]
                break

        problem = Problem(
            id=raw["questionId"],
            title=raw["title"],
            slug=raw["titleSlug"],
            difficulty=raw["difficulty"],
            description=raw["content"],
            code_stub=python3_stub,
        )
        log.info("Fetched problem #%s: %s (%s)", problem.id, problem.title, problem.difficulty)
        return problem

    def fetch_problem_list(self, category: str = "algorithms") -> list[dict]:
        page_size = 100
        skip = 0
        problems: list[dict] = []

        while True:
            data = self._query(_PROBLEMSET_QUERY, {
                "categorySlug": category,
                "limit": page_size,
                "skip": skip,
                "filters": {},
            })["problemsetQuestionList"]

            for q in data["questions"]:
                problems.append({
                    "id": q["questionFrontendId"],
                    "slug": q["titleSlug"],
                    "title": q["title"],
                    "difficulty": q["difficulty"],
                    "paid_only": q["isPaidOnly"],
                })

            total = data["total"]
            skip += page_size
            log.info("Fetched %d / %d problems", len(problems), total)

            if skip >= total:
                break

        return problems

    def _query(self, query: str, variables: dict) -> dict:

        response = httpx.post(
            self._url,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["data"]
