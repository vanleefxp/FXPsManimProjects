import numpy as np

__all__ = [
    "udvec",
]

def udvec ( angle: float ) -> np.ndarray:
    return np.array ((
        np.cos ( angle ),
        np.sin ( angle ),
        0,
    ))