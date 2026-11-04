import pytest
from lib.batching import chunk

def test_chunk_even():
    assert chunk([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]

def test_chunk_remainder():
    assert chunk([1, 2, 3], 2) == [[1, 2], [3]]

def test_chunk_rejects_nonpositive_size():
    with pytest.raises(ValueError):
        chunk([1], 0)
