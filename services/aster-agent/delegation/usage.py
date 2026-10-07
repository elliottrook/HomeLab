"""Allowlisted provider token snapshots; never infer cost or quota remaining."""
FIELDS = ("inputTokens", "cachedInputTokens", "outputTokens",
          "reasoningOutputTokens", "totalTokens")


def parse_usage(value):
    if not isinstance(value, dict):
        return None
    result = {}
    for section in ("last", "total"):
        data = value.get(section)
        if not isinstance(data, dict):
            return None
        clean = {}
        for key in FIELDS:
            number = data.get(key)
            if type(number) is not int or not 0 <= number <= 10**15:
                return None
            clean[key] = number
        number = data.get("cacheWriteInputTokens", 0)
        if type(number) is not int or not 0 <= number <= 10**15:
            return None
        clean["cacheWriteInputTokens"] = number
        result[section] = clean
    return result
