import numpy as np

from .numpy_utils import vectorize0dFix

@vectorize0dFix
@np.vectorize ( excluded = ( 1, ) )
def pitch2Freq ( pitch: float, a4Freq: float = 440 ) -> float:
    return a4Freq * 2 ** ( ( pitch - 69 ) / 12 )