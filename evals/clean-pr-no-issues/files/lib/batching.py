def chunk(items, size):
    """Split a list into consecutive lists of at most `size` elements."""
    if size <= 0:
        raise ValueError("size must be positive")
    return [items[i:i + size] for i in range(0, len(items), size)]
