from collections.abc import Sequence, Iterable
from typing import TypeVar

from manim import *
from svgelements import Path as SVGPath

__all__ = [ 
    "PianoKeyboard", "MultiOctavePianoKeyboard",
    "MARK_RED", "MARK_GREEN", "MARK_BLUE",
]

M = TypeVar ( "M", bound = Mobject )
_MarkColorType = tuple [ ManimColor, ManimColor ]

_keys = (
    ( False, 0 ),
    ( True, 0 ),
    ( False, 1 ),
    ( True, 1 ),
    ( False, 2 ),
    ( False, 3 ),
    ( True, 2 ),
    ( False, 4 ),
    ( True, 3 ),
    ( False, 5 ),
    ( True, 4 ),
    ( False, 6 ),
)

MARK_RED = ( RED_B, RED_D )
MARK_GREEN = ( GREEN_B, GREEN_D )
MARK_BLUE = ( BLUE_B, BLUE_D )

class _PianoKeyboardKeyAccessor ( Sequence [ Mobject ] ):
    def __init__ ( self, parent: "PianoKeyboard" ):
        self._parent = parent
    
    def __len__ ( self ) -> int: return 12
    
    def __getitem__ ( self, idx: int ) -> Mobject:
        isBlack, groupIndex = _keys [ idx ]
        if isBlack: return self._parent._blackKeys [ groupIndex ]
        else: return self._parent._whiteKeys [ groupIndex ]

class _PianoKeyboardSubmobAccessor ( ):
    def __init__ ( self, parent: "PianoKeyboard" ):
        self._parent = parent
        self._keys = _PianoKeyboardKeyAccessor ( parent )
    
    @property
    def blackKeys ( self ) -> VGroup:
        return self._parent._blackKeys
    
    @property
    def whiteKeys ( self ) -> VGroup:
        return self._parent._whiteKeys
    
    @property
    def keys ( self ) -> _PianoKeyboardKeyAccessor:
        return self._keys
    
class PianoKeyboard ( VGroup ):
    def __init__ ( 
            self, /, 
            whiteWidth = 0.5,
            whiteHeight = 2.5,
            blackWidth = 0.25,
            blackHeight = 1.5,
            cornerWidth = 0.08,
            blackDisplace = ( -0.1, 0.1, -0.1, 0, 0.1 ),
            markColor: _MarkColorType = MARK_BLUE,
            **kwargs, 
        ):
        
        super ( ).__init__ ( )
        
        ww, hw = whiteWidth, whiteHeight
        wb, hb = blackWidth, blackHeight
        c = cornerWidth
        
        self._mobs = _PianoKeyboardSubmobAccessor ( self )
        self._markColor = markColor
        self._markedKeys = set ( )
        
        mob_whiteKeyTemplate = VMobjectFromSVGPath ( 
            SVGPath ( 
                f"m 0,0 "
                f"h {ww} "
                f"v {-hw + c} "
                f"q 0,{-c} {-c},{-c} " 
                f"h {-ww + 2 * c}"
                f"q {-c},0 {-c},{c} "
                "z"
            ),
            fill_color = WHITE,
            stroke_color = GRAY,
            stroke_width = 2,
            fill_opacity = 1,
        )
        mob_blackKeyTemplate = VMobjectFromSVGPath ( 
            SVGPath ( 
                f"m 0,0 "
                f"h {wb} "
                f"v {-hb + c} "
                f"q 0,{-c} {-c},{-c} " 
                f"h {-wb + 2 * c}"
                f"q {-c},0 {-c},{c} "
                "z"
            ),
            fill_color = BLACK,
            stroke_color = GRAY_D,
            stroke_width = 2,
            fill_opacity = 1,
        )
        
        self._whiteKeys = VGroup ( )
        self._blackKeys = VGroup ( )
        
        for i in range ( 7 ):
            mob_whiteKey = mob_whiteKeyTemplate.copy ( )\
                .shift ( ( i * ww, 0, 0 ) )
            mob_whiteKey.isBlack = False
            self._whiteKeys.add ( mob_whiteKey )
        
        for i, dx in zip ( ( 0, 1, 3, 4, 5 ), blackDisplace ):
            blackX = ( i + 1 ) * ww  + wb * ( dx - 0.5 )
            mob_blackKey = mob_blackKeyTemplate.copy ( )\
                .shift ( ( blackX, 0, 0 ) )
            mob_blackKey.isBlack = True
            self._blackKeys.add ( mob_blackKey )
        
        self.add ( self._whiteKeys, self._blackKeys )
    
    @property
    def mobs ( self ) -> _PianoKeyboardSubmobAccessor:
        return self._mobs
    
    def markKey ( 
            self, key: int, /, 
            markColor: _MarkColorType | None = None,
    ):
        if markColor is None: markColor = self._markColor
        isBlack = _keys [ key ] [ 0 ]
        color = markColor [ isBlack ]
        mob_key = self.mobs.keys [ key ]
        mob_key.set_fill ( color = color )
        self._markedKeys.add ( key )
        return self
    
    def markKeys ( 
            self, keys: Iterable [ int ], /, 
            markColor: _MarkColorType | None = None 
    ):
        for key in keys:
            self.markKey ( key, markColor = markColor )
        return self
    
    def unmarkKey ( self, key: int ):
        isBlack = _keys [ key ] [ 0 ]
        self._markedKeys.discard ( key )
        mob_key = self.mobs.keys [ key ]
        mob_key.set_fill ( color = BLACK if isBlack else WHITE )
        return self
    
    def unmarkKeys ( self, keys: Iterable [ int ] ):
        for key in keys:
            self.unmarkKey ( key )
        return self
    
    def resetMarks ( self ):
        self.unmarkKeys ( frozenset ( self._markedKeys ) )
        return self

class MultiOctavePianoKeyboard ( VGroup ):
    def __init__ ( 
            self, octaves = 2,
            whiteWidth = 0.5,
            **kwargs 
    ):
        super ( ).__init__ ( )
        wo = whiteWidth * 7
        mob_keyboardTemplate = PianoKeyboard ( whiteWidth = whiteWidth, **kwargs )
        
        for i in range ( octaves ):
            mob_keyboard = mob_keyboardTemplate.copy ( )\
                .shift ( ( i * wo, 0, 0 ) )
            self.add ( mob_keyboard )
    
    def markKey ( 
            self, key: int, /, 
            markColor: _MarkColorType | None = None 
    ):
        octave, idx = divmod ( key, 12 )
        self [ octave ].markKey ( idx, markColor = markColor )
        return self
    
    def getKey ( self, key: int ) -> Mobject:
        octave, idx = divmod ( key, 12 )
        return self [ octave ].mobs.keys [ idx ]
    
    def markKeys ( 
            self, keys: Iterable [ int ], /, 
            markColor: _MarkColorType | None = None 
    ):
        for key in keys:
            self.markKey ( key, markColor = markColor )
        return self
    
    def unmarkKey ( self, key: int ):
        octave, idx = divmod ( key, 12 )
        self [ octave ].unmarkKey ( idx )
        return self
    
    def unmarkKeys ( self, keys: Iterable [ int ] ):
        for key in keys:
            self.unmarkKey ( key )
        return self
    
    def resetMarks ( self ):
        for mob_keyboard in self:
            mob_keyboard.resetMarks ( )
        return self
    
    def alignToKey ( self, key: int, mob: M, buff: float = 0.2 ) -> M:
        mob_key = self.getKey ( key )
        mob.move_to ( mob_key )\
            .align_to ( mob_key, DOWN )\
            .shift ( UP * buff )
        return mob