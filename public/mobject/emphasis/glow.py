from typing import TypeVar
from manim import *

__all__ = [ "addGlow", "Glow" ]

M = TypeVar ( "M", bound = Mobject )

def addGlow ( mob: M, **kwargs ) -> M:
    glow = Glow ( **kwargs ).move_to ( mob )
    mob.add ( glow )
    return mob

class Glow ( VGroup ):
    def __init__ ( 
        self,
        radius = 1,
        color = YELLOW,
        **kwargs,
    ):
        super ( ).__init__ ( **kwargs )
        for idx in range ( 60 ):
            mob_circle = Circle ( 
                radius = radius * ( 1.002 ** ( idx ** 2 ) ) / 400, 
                stroke_opacity = 0, 
                fill_color = color,
                fill_opacity = 0.2 - idx / 300
            )
            self.add ( mob_circle )
        self.set_z_index ( -1 )