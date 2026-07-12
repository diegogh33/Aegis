from enum import Enum


class Recommendation(str, Enum):
    STRONG_BUY = "Strong Buy"

    BUY = "Buy"

    WATCH = "Watch"

    REJECT = "Reject"