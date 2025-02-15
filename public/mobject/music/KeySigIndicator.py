from manim import *
from ...text_config import *

__all__ = [ "KeySigIndicator" ]

_sharpText  = (
    r"{\sh}F",
    r"{\sh}C",
    r"{\sh}G",
    r"{\sh}D",
    r"{\sh}A",
    r"{\sh}E",
    r"{\sh}B"
)

_flatText = (
    r"{\fl}B",
    r"{\fl}E",
    r"{\fl}A",
    r"{\fl}D",
    r"{\fl}G",
    r"{\fl}C",
    r"{\fl}F",
)

class _KeySigIndicatorSubmobAccessor ( ):
    def __init__ ( self, parent: "KeySigIndicator" ):
        self._parent = parent
    
    @property
    def sharps ( self ):
        return self._parent._mob_sharps
    
    @property
    def flats ( self ):
        return self._parent._mob_flats

class KeySigIndicator ( VGroup ):
    """
    Mobject indicating the number of sharps / flats in a key signature.
    """
    
    def __init__(
        self, acciCount: int = 0,
        width = 5,
        height = 0.3,
        gap = 0.05, 
        fs = 0.8,
        **kwargs,
    ):
        super ( ).__init__ ( **kwargs )
        
        blockWidth = ( width - 13 * gap ) / 14
        
        self._mobs = _KeySigIndicatorSubmobAccessor ( self )
        self._mob_sharps = VGroup ( )
        self._mob_flats = VGroup ( )
        
        for i in range ( 7 ):
            mob_sharpBlock = VGroup ( )
            mob_sharpBlockBg = Rectangle ( 
                width = blockWidth, 
                height = height,
                color = RED,
                fill_opacity = 1,
                stroke_width = 0,
            ).shift ( ( i + 0.5 ) * ( blockWidth + gap ) * RIGHT )
            mob_sharpText = Tex ( 
                _sharpText [ i ], 
                color = RED, 
                **newLatexConfig ( fs = fs ),
            ).next_to ( mob_sharpBlockBg, DOWN, buff = 0.1 )
            mob_sharpBlock.add ( mob_sharpBlockBg, mob_sharpText )
            self._mob_sharps.add ( mob_sharpBlock )
        
        for i in range ( 7 ):
            mob_flatBlock = VGroup ( )
            mob_sharpBlockBg = Rectangle ( 
                width = blockWidth, 
                height = height,
                color = GREEN,
                fill_opacity = 1,
                stroke_width = 0,
            ).shift ( ( i + 0.5 ) * ( blockWidth + gap ) * LEFT )
            mob_flatText = Tex ( 
                    _flatText [ i ], 
                    color = GREEN, 
                    **newLatexConfig ( fs = fs ),
            ).next_to ( mob_sharpBlockBg, DOWN, buff = 0.1 )
            mob_flatBlock.add ( mob_sharpBlockBg, mob_flatText )
            self._mob_flats.add ( mob_flatBlock )
        
        self.add ( self._mob_sharps, self._mob_flats )
        self.setAcciCount ( acciCount )
    
    @property
    def mobs ( self ) -> _KeySigIndicatorSubmobAccessor:
        return self._mobs
    
    def setAcciCount ( self, acciCount: int ):
        for i, mob_sharpBlock in enumerate ( self._mob_sharps ):
            if i < acciCount: mob_sharpBlock.set_opacity ( 1 )
            else: mob_sharpBlock.set_opacity ( 0.25 )
        for i, mob_flatBlock in enumerate ( self._mob_flats ):
            if i < -acciCount: mob_flatBlock.set_opacity ( 1 )
            else: mob_flatBlock.set_opacity ( 0.25 )
            