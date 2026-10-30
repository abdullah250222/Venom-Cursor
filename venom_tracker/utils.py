import math

def clamp(value, low, high):
    """Keep a value within a specified range."""
    return max(low, min(high, value))


def distance(point_a, point_b):
    """Calculate the distance between two points."""
    dx = point_a[0] - point_b[0]
    dy = point_a[1] - point_b[1]

    return math.hypot(dx, dy)