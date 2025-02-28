from typing import TypeVar
from collections.abc import Iterable, Sequence

import numpy as np
from sklearn.cluster import DBSCAN

__all__ = [
    "nextPowerOf2", 
    "prevPowerOf2",
    "loop",
    "nextMultipleOf",
    "prevMultipleOf",
    "approxGCD",
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

def _clusterCenters ( data: np.ndarray, labels ):
    nClusters = np.max ( labels ) + 1
    centers = np.empty ( nClusters, dtype = float )
    for i in range ( nClusters ):
        cluster = data [ labels == i ]
        centers [ i ] = np.mean ( cluster )
    return centers

def approxGCD ( data: Iterable [ float ], tolerance: float ) -> float:
    """
    find a value `k` such that all data elements are approximately multiples of `k`
    """
    dbscan = DBSCAN ( eps = tolerance, min_samples = 1 )
    data = np.array ( data, dtype = float )
    while len ( data ) > 1:
        # remove elements close to zero
        # otherwise the algorithm might never terminate
        data = data [ abs ( data ) > tolerance ]
        data.sort ( )
        data = data - np.insert ( data, 0, 0 ) [ :-1 ]
        clusterResult = dbscan.fit ( data.reshape ( -1, 1 ) )
        labels = clusterResult.labels_
        data = _clusterCenters ( data, labels )
    return data [ 0 ]
