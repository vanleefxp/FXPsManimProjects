from collections.abc import Callable
import numpy as np

def vectorize0dFix ( func ):
    def _func ( *args, **kwargs ):
        result = func ( *args, **kwargs )
        if isinstance ( result, np.ndarray ) and result.shape == ( ):
            return result.item ( )
        else:
            return result
    return _func

def asVarArg ( fn: Callable ):
     return lambda *args: fn ( np.array ( args ) )
