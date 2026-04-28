class LeetCodeAPIError(Exception):
    pass


class RateLimitedError(LeetCodeAPIError):
    pass


class ModelError(Exception):
    pass


class CodeExtractionError(Exception):
    pass
