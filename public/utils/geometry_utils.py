from manim.typing import Point3D

import numpy as np
import numpy.typing as npt

from .numpy_utils import vectorize0dFix

__all__ = [
    "P",
    "udvec",
    "rescale",
    "coordSystemConverter",
    "RangesLike",
]

type RangesLike = npt.NDArray [ np.floating ]

def P ( *args: float, dim: int = 3 ) -> Point3D:
    """
    A shortcut for creating points. You may pass either 2 or 3 arguments for creating 2D or 3D 
    points.
    """
    p = np.empty ( dim )
    l = len ( args )
    p [ :l ] = args
    p [ l: ] = 0
    return p

def udvec ( angle: float ) -> np.ndarray:
    return np.array ((
        np.cos ( angle ),
        np.sin ( angle ),
        0,
    ))

def rescale ( 
    value: float, 
    srcMin: float,
    srcMax: float,
    dstMin: float = 0,
    dstMax: float = 1,
) -> float:
    t = ( value - srcMin ) / ( srcMax - srcMin )
    return dstMin + t * ( dstMax - dstMin )

class coordSystemConverter ( ):
    def __init__ ( 
            self, 
            srcRanges: RangesLike, 
            dstRanges: RangesLike, 
    ):
        self._srcRanges = np.array ( srcRanges )
        self._dstRanges = np.array ( dstRanges )
        self._srcRanges.flags.writeable = False
        self._dstRanges.flags.writeable = False
    
    def src2dst ( self, *srcCoords: float ) -> np.ndarray:
        return rescale ( np.array ( srcCoords ), *self._srcRanges.T, *self._dstRanges.T )
    
    def dst2src ( self, *dstCoords: float ) -> np.ndarray:
        return rescale ( np.array ( dstCoords ), *self._dstRanges.T, *self._srcRanges.T )