from typing import Generic, TypeVar
from manim import *

__all__ = [ 
    "withOutlineBackground",
    "WithBackground", "TextWithBackground",
]

M = TypeVar ( "M", bound = VMobject )
type TextMobject = Text | SingleStringMathTex
TM = TypeVar ( "TM", bound = TextMobject )

def withOutlineBackground ( 
        mob: TM, width: float = 8, 
        opacity = 0.75 
) -> TM:
    return mob.set_stroke ( 
        background = True,
        width = width,
        opacity = opacity,
        color = config.background_color,
    )

class WithBackground ( Generic [ M ], VGroup ):
    def __init__ ( 
        self, mobject: M, 
        opacity = 0.5,
        buff = 0.1,
        **kwargs
    ):
        super ( ).__init__ ( 
            BackgroundRectangle ( mobject, buff = buff )\
                .set_fill ( opacity = opacity ),
            mobject,
            **kwargs,
        )
        self._original = mobject
    
    @property
    def original ( self ):
        return self._original

class TextWithBackground ( WithBackground [ TM ] ):
    def __init__ ( self, textMobject: TM, **kwargs ):  
        super ( ).__init__ ( textMobject, **kwargs )
    
    @property
    def font_size ( self ):
        return self.original.font_size
    
    @font_size.setter
    def font_size ( self, value: float ):
        self.original.font_size = value