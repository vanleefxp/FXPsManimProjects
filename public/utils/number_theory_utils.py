from typing import TypeVar
from collections.abc import Sequence
# import numpy as np

__all__ = [
    "nextPowerOf2", 
    "prevPowerOf2",
    "loop",
    "nextMultipleOf",
    "prevMultipleOf",
]

# @np.vectorize 
def nextPowerOf2 ( n: int ) -> int:
    if n <= 0:
        return 1
    result = 1
    power = 0
    while result < n:
        result <<= 1
        power += 1
    return result, power

def prevPowerOf2 ( n: int ) -> int:
    result, power = nextPowerOf2 ( n )
    result >>= 1
    power -= 1
    return result, power

T = TypeVar ( "T" )
def loop ( lst: Sequence [ T ], idx: int ) -> T:
    return lst [ idx % len ( lst ) ]

def nextMultipleOf ( n: float, k: float, strict: bool = True ) -> float:
    """
    Returns the smallest integer multiple of `k` greater than `n`.
    """
    if strict and n % k == 0: return n + k
    return ( n + k - 1 ) // k * k

def prevMultipleOf ( n: float, k: float, strict: bool = True ) -> float:
    """
    Returnes the largest integer multiple of `k` less than `n`.
    """
    if strict and n % k == 0: return n - k
    return n // k * k
