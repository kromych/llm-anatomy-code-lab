"""Small statistics helpers."""


def mean(xs):
    return sum(xs) / len(xs)


def median(xs):
    s = sorted(xs)
    mid = len(s) // 2
    if len(s) % 2 == 1:
        return s[mid]
    return (s[mid] + s[mid + 1]) / 2


def spread(xs):
    return max(xs) - min(xs)
