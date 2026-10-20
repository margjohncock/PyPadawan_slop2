"""Scale individual measurements."""
DEFAULT_FACTOR = 2


def scale(value, factor=DEFAULT_FACTOR):
    """Multiply value by factor. The default factor doubles the value."""
    return value * factor
