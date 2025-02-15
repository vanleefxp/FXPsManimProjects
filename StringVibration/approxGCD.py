from collections.abc import Iterable

import numpy as np
from sklearn.cluster import DBSCAN

__all__ = [ "approxGCD" ]

def clusterCenters ( data: np.ndarray, labels ):
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
        data = clusterCenters ( data, labels )
    return data [ 0 ]

if __name__ == "__main__":
    # Example 1
    data = np.array ( ( 500, 600, 700, 800, 900 ), dtype = float )
    data += np.random.uniform ( -2, 2, size = len ( data ) )
    np.random.shuffle ( data )
    print ( data )
    print ( approxGCD ( data, 50 ) )
    
    # Example 2
    data = np.array ( ( 3, 6, 15, 21, 24, 30 ), dtype = float )
    data += np.random.uniform ( -0.01, 0.01, size = len ( data ) )
    np.random.shuffle ( data )
    print ( data )
    print ( approxGCD ( data, 1 ) ) 
    