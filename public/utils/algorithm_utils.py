from typing import Iterable, Set
import numpy as np

def segStack ( segs: np.ndarray ) -> Iterable [ Set [ int ] ]:
    segs = np.array ( segs )
    if len ( segs ) == 0: return 
    segArgs = np.argsort ( segs [ :, 1 ] )
    segs = segs [ segArgs ]
    remainingSegs = np.arange ( len ( segs ) )
    while len ( remainingSegs ) > 0:
        layer = set ( )
        last = None
        for i in remainingSegs:
            seg = segs [ i ]
            if last is None or last [ 1 ] <= seg [ 0 ]:
                layer.add ( segArgs [ i ] )
                last = seg
        yield frozenset ( layer )
        remainingSegs = np.array ([ 
            i for i in remainingSegs 
            if i not in layer 
        ])