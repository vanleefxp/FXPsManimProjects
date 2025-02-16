from typing import TypeVar
from manim import *

__all__ = [ "stableNextTo" ]

M = TypeVar ( "M", bound = Mobject )
def stableNextTo (
    mob1: M, mob2: Mobject, 
    direction = RIGHT, 
    buff = MED_SMALL_BUFF, **kwargs 
) -> M:
    """
    Similar to `Mobject.next_to()`, but will not change the coordinate on the dimensions where 
    `direction` is 0.
    """
    oldCenter = mob1.get_center ( )
    mob1.next_to ( mob2, direction, buff = buff, **kwargs )
    for i, d in enumerate ( direction ):
        if d == 0:
            mob1.set_coord ( oldCenter [ i ], i )
    return mob1