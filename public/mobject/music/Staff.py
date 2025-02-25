from typing import TypeVar, Generic, Iterator
from collections.abc import Iterable
from abc import ABCMeta
from typing import Self
from pathlib import Path
from functools import lru_cache
import itertools as it

from manim import *
from manim.typing import Point3D
import pyrsistent as pyr

from ...utils.algorithm_utils import segStack
from ..PositionedMobject import PositionedMobject

DIR = Path ( __file__ ).parent if "__file__" in locals ( ) else Path.cwd ( )

S = TypeVar ( "S", bound = "StaffElement" )

_sharpPositions = pyr.m (
    G = ( 4, 1, 5, 2, -1, 3, 0 ),
    F = ( 2, -1, 3, 0, -3, 1, -2 ),
)

_flatPositions = pyr.m (
    G = ( 0, 3, -1, 2, -2, 1, -3 ),
    F = ( -2, 1, -3, 0, 3, -1, 2 ),
)

_clefCodepoints = pyr.pmap ( {
    "G": "\ue050",
    "F": "\ue062",
    "C": "\ue05c",
    "G_change": "\ue07a",
    "F_change": "\ue07c",
    "C_change": "\ue07b",
} )

_noteheadCodepoints = pyr.pmap ( {
    "doubleWhole": "\ue0a0",
    "whole": "\ue0a2",
    "half": "\ue0a3",
    "black": "\ue0a4",
} )

_clefDefaultVPos = pyr.pmap ( { 
    "G": -2,
    "F": 2,
    "C": 0,
} )

TRIPLE_SHARP = 3
DOUBLE_SHARP = 2
SHARP = 1
NATURAL = 0
FLAT = -1
DOUBLE_FLAT = -2
TRIPLE_FLAT = -3

_accidentalCodepoints = pyr.pmap ( {
    TRIPLE_SHARP: "\ue265",
    DOUBLE_SHARP: "\ue263",
    SHARP: "\ue262",
    NATURAL: "\ue261",
    FLAT: "\ue260",
    DOUBLE_FLAT: "\ue264",
    TRIPLE_FLAT: "\ue266",
} )

@lru_cache
def _musicGlyphMetrics ( glyph: str, musicFont: str ) -> np.ndarray:
    # because Manim has no direct method to align text on baseline, so this function is introduced
    # create a text Mobject with the desired glyph and a black notehead
    # the black notehead's center y position is the baseline of the music font
    # in font size 288, 1 sp = 1 Manim unit
    mob_text = Text ( f"{glyph}\ue0a4", font = musicFont, font_size = 288 )
    targetChar, refChar = mob_text [ :-1 ], mob_text [ -1 ]
    y1 = targetChar.get_center ( ) [ 1 ]
    y_top = targetChar.get_critical_point ( UP ) [ 1 ]
    y_bottom = targetChar.get_critical_point ( DOWN ) [ 1 ]
    y_ref = refChar.get_center ( ) [ 1 ]
    return np.array (( y1 - y_ref, y_bottom - y_ref, y_top - y_ref ))

class MusicGlyph ( Text, PositionedMobject ):
    """
    Represents an SMuFL music glyph.
    """
    
    def __init__ ( 
            self, 
            glyph: str, 
            musicFont: str = "Bravura",
            sp: float = 0.25, 
            **kwargs 
    ):
        super ( ).__init__ ( 
            text = glyph, 
            font = musicFont, 
            font_size = 288 * sp, 
            **kwargs 
        )
        self._d = _musicGlyphMetrics ( glyph, musicFont ) [ 0 ]
        self._sp = sp
        self.shift ( self._d * sp * UP )
    
    def getPosition ( self ) -> Point3D:
        return self.get_center ( ) + self._d * self.sp * DOWN
    
    @property
    def sp ( self ) -> float: return self._sp

class StaffElement ( VGroup, metaclass = ABCMeta ):
    def __init__ ( self, parent: "Staff", **kwargs ):
        super ( ).__init__ ( **kwargs )
        self._parent = parent
    
    @property
    def sp ( self ) -> float: return self.parent.sp
    @property
    def musicFont ( self ) -> str: return self.parent.musicFont
    @property
    def parent ( self ) -> "Staff": return self._parent
    
    def getStartHpos ( self ) -> float:
        """Start position of the element on the staff measured in staff space (sp)."""
        x1 = self.get_critical_point ( UL ) [ 0 ]
        x2 = self._parent.getPosition ( ) [ 0 ]
        return ( x1 - x2 ) / self.sp
    
    def getEndHpos ( self ) -> float:
        """End position of the element on the staff measured in staff space (sp)."""
        x1 = self.get_critical_point ( UR ) [ 0 ]
        x2 = self._parent.getPosition ( ) [ 0 ]
        return ( x1 - x2 ) / self.sp
    
    def before ( self, other: "StaffElement | float", buff: float = 0 ) -> Self:
        """
        Place the current element after the other element or a horizontal position.
        """
        if not isinstance ( other, Mobject ):
            other = self.parent.getPosition ( ) + other * self.sp * RIGHT
        self.next_to ( other, LEFT, buff = buff * self.sp, coor_mask = RIGHT )
        return self
    
    def after ( self, other: "StaffElement | float", buff: float = 0 ) -> Self:
        """
        Place the current element after the other element or a horizontal position.
        """
        if not isinstance ( other, Mobject ):
            other = self.parent.getPosition ( ) + other * self.sp * RIGHT
        self.next_to ( other, RIGHT, buff = buff * self.sp, coor_mask = RIGHT )
        return self
    
    def getHspan ( self ) -> float:
        """
        Horizontal span of the element on the staff measured in staff space (sp).
        """
        return self.get_width ( ) / self.sp
    
    def shiftHpos ( self, delta: float ) -> Self:
        self.shift ( delta * self.sp * RIGHT )
        return self
    
class PositionedStaffElement ( StaffElement, PositionedMobject ):
    def __init__ ( self, parent, **kwargs ):
        super ( ).__init__ ( parent, **kwargs )
        self._mob_startingPoint = Dot ( radius = 0.01 )\
            .shift ( parent.getPosition ( ) )
        self.add ( self._mob_startingPoint )
        
    def getHpos ( self ) -> float:
        """Horizontal position of the element measured in staff space (sp)."""
        x1 = self.getPosition ( ) [ 0 ]
        x2 = self._parent.getPosition ( ) [ 0 ]
        return ( x1 - x2 ) / self.sp
    
    def setHpos ( self, hpos: float ) -> Self:
        """Set the horizontal position of the element measured in staff space (sp)."""
        currentHpos = self.getHpos ( )
        self.shift ( ( hpos - currentHpos ) * self.sp * RIGHT )
        return self
    
    def getPosition ( self ) -> np.ndarray:
        """Position of the element on screen. In Manim coordinate unit."""
        return self._mob_startingPoint.get_center ( )
    
    def getLeftHspan ( self ) -> float:
        """
        Left horizontal span of the element on the staff measured in staff space (sp).
        Defined as the position of the left most point on this element relative to the 
        element's position.
        """
        x1 = self.get_critical_point ( UL ) [ 0 ]
        x2 = self.getPosition ( ) [ 0 ]
        return ( x1 - x2 ) / self.sp
    
    def getRightHspan ( self ) -> float:
        """
        Right horizontal span of the element on the staff measured in staff space (sp).
        Defined as the position of the right most point on this element relative to the 
        element's position.
        """
        x1 = self.get_critical_point ( UR ) [ 0 ]
        x2 = self.getPosition ( ) [ 0 ]
        return ( x1 - x2 ) / self.sp

class StaffElementGroup ( Generic [ S ], StaffElement ):
    def __init__ ( self, parent: "Staff", *submobjects: "StaffElement", **kwargs ):
        super ( ).__init__ ( parent, **kwargs )
        self.add ( *submobjects )
    
    def __getitem__ ( self, value ) -> S:
        return super ( ).__getitem__ ( value )
    
    def __iter__ ( self ) -> Iterator [ S ]:
        return super ( ).__iter__ ( )

class Clef ( PositionedStaffElement ):
    def __init__ ( 
            self, parent: "Staff", 
            clefType: str = "G", 
            change: bool = False,
            valt: int = 0,
            **kwargs 
    ):
        super ( ).__init__ ( parent, **kwargs )
        sp = self.sp
        musicFont = self.musicFont
        
        if change:
            clefKey = f"{clefType}_change"
            k = 1.5 * self.parent.changeClefScale
        else:
            clefKey = clefType
            k = 1
        
        glyph = _clefCodepoints [ clefKey ]
        self._clefType = clefType
        self._change = change
        self._defaultVpos = defaultVPos = _clefDefaultVPos [ clefType ]
        self._valt = valt
        
        self._mob_text = MusicGlyph (
            glyph,
            musicFont = musicFont,
            sp = sp * k,
        )   .shift ( UP * ( sp * ( ( valt + defaultVPos ) / 2 ) ) )\
            .shift ( self.parent.getPosition ( ) )
        
        self.add ( self._mob_text )
    
    @property
    def defaultVpos ( self ) -> int:
        """
        Default vertical position of the clef on the staff measured in half staff space (0.5 sp).
        This returns the default position of the clef according to its type.
        """
        return self._defaultVpos
    
    @property
    def vpos ( self ) -> int:
        """
        Vertical position of the clef on the staff measured in half staff space (0.5 sp).
        This returns the actual position of the clef on the staff, taking into account the 
        vertical adjustment.
        """
        return self._defaultVpos + self._valt
    
    @property
    def valt ( self ) -> int:
        """
        Vertical adjustment of the clef on the staff measured in half staff space (0.5 sp).
        This returns the vertical adjustment relative to its default position.
        """
        return self._valt
    
    @property
    def change ( self ) -> bool:
        """Whether the clef is a change clef."""
        return self._change
    
    @property
    def clefType ( self ) -> str:
        """Type of the clef."""
        return self._clefType
    
    def getScaleCenter ( self ) -> Point3D:
        return self.getPosition ( ) + UP * ( self.sp * self.vpos / 2 )
        
class KeySignature ( PositionedStaffElement ):
    def __init__ ( 
            self, parent: "Staff", 
            clefType: str = "G",
            acciCount: int = 0,
            **kwargs 
    ):
        super ( ).__init__ ( parent, **kwargs )
        
        self._clefType = clefType
        self._acciCount = acciCount
        
        self._mob_accidentals = VGroup ( )
        
        sp = self.sp
        acciAdvance = self.parent.keySigAcciAdvance
        musicFont = self.musicFont
        
        if acciCount > 0:
            mob_sharpTemplate = MusicGlyph ( "\ue262", musicFont = musicFont, sp = sp )
            n = abs ( acciCount )
            for i in range ( n ):
                x = i * acciAdvance * sp
                y = _sharpPositions [ clefType ] [ i ] * sp / 2
                mob_sharp = mob_sharpTemplate.copy ( ).toPosition ( ( x, y, 0 ) )
                self._mob_accidentals.add ( mob_sharp )
            self._mob_accidentals.shift ( parent.getPosition ( ) )
        elif acciCount < 0:
            mob_flatTemplate = MusicGlyph ( "\ue260", musicFont = musicFont, sp = sp )
            n = abs ( acciCount )
            for i in range ( n ):
                x = i * acciAdvance * sp
                y = _flatPositions [ clefType ] [ i ] * sp / 2
                mob_flat = mob_flatTemplate.copy ( ).toPosition ( ( x, y, 0 ) )
                self._mob_accidentals.add ( mob_flat )
            self._mob_accidentals.shift ( parent.getPosition ( ) )
        else:
            self._mob_accidentals.add ( self._mob_startingPoint.copy ( ) )
        
        self.add ( self._mob_accidentals )
    
    @property
    def clefType ( self ) -> str:
        """Type of the clef."""
        return self._clefType
    
    @property
    def acciCount ( self ) -> int:
        """
        Number of sharps or flats in the key signature.
        Positive for sharps, negative for flats.
        """
        return self._acciCount
    
    def getAccidental ( self, idx: int ) -> Text:
        if self.acciCount == 0:
            raise IndexError ( "No accidentals in this key signature." )
        return self._mob_accidentals [ idx ]
    
    def accidentals ( self ) -> Iterable [ Text ]:
        if self.acciCount == 0: return 
        yield from self._mob_accidentals

class Barline ( PositionedStaffElement ):
    def __init__ ( 
            self, parent: "Staff",
            lineStyle: str = "solid", 
            **kwargs,
    ):
        super ( ).__init__ ( parent, **kwargs )
        
        self._lineStyle = lineStyle
        
        sp = self.sp
        th = self.parent.barlineThickness
        match lineStyle:
            case "solid":
                self._mob_line = Line ( 
                    ( 0, 2 * sp, 0 ), ( 0, -2 * sp, 0 ),
                    stroke_width = th,
                )
            case "dashed":
                l1, l2 = self.parent.barlineDashLength
                l1 *= sp; l2 *= sp
                ratio = l1 / ( l1 + l2 )
                self._mob_line = DashedLine ( 
                    ( 0, 2 * sp, 0 ), ( 0, -2 * sp, 0 ), 
                    dash_length = l1, dashed_ratio = ratio,
                    stroke_width = th,
                )
            case "double": 
                distance = self.parent.doubleBarlineDistance * sp
                self._mob_line = VGroup ( )
                lineTemplate = Line ( 
                    ( 0, 2 * sp, 0 ), ( 0, -2 * sp, 0 ),
                    stroke_width = th,
                )
                self._mob_line.add (
                    lineTemplate.copy ( )\
                        .shift ( ( -distance / 2, 0, 0 ) ),
                    lineTemplate.copy ( )\
                        .shift ( ( distance / 2, 0, 0 ) ),
                )
            case _:
                raise ValueError ( f"Invalid line style: {lineStyle}" )
    
        self.add ( self._mob_line.shift ( self.getPosition ( ) ) )
    
    @property
    def lineStyle ( self ) -> str:
        """Style of the barline."""
        return self._lineStyle

class Chord ( PositionedStaffElement ):
    def __init__ ( 
            self, parent,
            vpos: Iterable [ int ],
            ledgerLineLength: float | tuple [ float, float ] | None = 1/3,
            noteheadType: str | Iterable [ str ] = "black",
            accidentals: None | Iterable [ int | None ] = None,
            **kwargs 
    ):
        super ( ).__init__ ( parent, **kwargs )
        
        sp = self.sp
        musicFont = self.musicFont
        musicFontSize = self.parent._musicFontSize
        
        vpos = np.array ( vpos )
        if isinstance ( noteheadType, str ):
            noteheadType = np.full ( len ( vpos ), noteheadType )
        else: noteheadType = np.array ( noteheadType )
        vposArgs = np.argsort ( vpos )
        
        vpos = vpos [ vposArgs ]
        noteheadType = noteheadType [ vposArgs ]
        low, high = vpos [ 0 ], vpos [ -1 ]
        
        if accidentals is None:
            accidentals = it.repeat ( None )
        else:
            accidentals = np.array ( accidentals ) [ vposArgs ]
        
        @lru_cache ( maxsize = 4 )
        def getNoteheadTemplate ( noteheadType: str = "black" ) -> Text:
            mob_noteheadTemplate = MusicGlyph ( 
                _noteheadCodepoints [ noteheadType ], 
                musicFont = musicFont,
                sp = sp,
            ).move_to ( ORIGIN )
            noteheadWidth = mob_noteheadTemplate.get_width ( )
            mob_noteheadTemplate.shift ( ( -noteheadWidth / 2, 0, 0 ) )
            return mob_noteheadTemplate
        
        # create ledger lines
        
        if ledgerLineLength is not None and ( low < -5 or high > 5 ):
            noteheadWidth = getNoteheadTemplate ( 
                "whole" if "whole" in noteheadType 
                else "black" 
            ).get_width ( )
            th = self.parent.ledgerLineThickness
            
            if isinstance ( ledgerLineLength, float ):
                ledgerLeft = ledgerRight = ledgerLineLength
            else: ledgerLeft, ledgerRight = ledgerLineLength 
            
            mob_ledgerLineTemplate = Line (
                ( -ledgerLeft * sp - noteheadWidth, 0, 0 ),
                ( ledgerRight * sp, 0, 0 ),
                stroke_width = th,
            )
            self._mob_ledgerLines = StaffElement ( self.parent )
            if low < -5:
                # add ledger lines below
                numLines = ( -low - 4 ) // 2
                for i in range ( numLines ):
                    y = ( -i - 3 ) * sp
                    self._mob_ledgerLines.add (
                        mob_ledgerLineTemplate.copy ( )\
                            .shift ( UP * y )
                    )
            
            if high > 5:
                # add ledger lines above
                numLines = ( high - 4 ) // 2
                for i in range ( numLines ):
                    y = ( i + 3 ) * sp
                    self._mob_ledgerLines.add (
                        mob_ledgerLineTemplate.copy ( )\
                            .shift ( UP * y )
                    )
                    
            self._mob_ledgerLines.shift ( self.parent.getPosition ( ) )
            self.add ( self._mob_ledgerLines )
        
        self._mob_noteheads = StaffElement ( self.parent )
        lastFlipped = False
        lastVpos = None
        lmob_accidentals = [ ]
        accidentalSegs = [ ]
        self._accidentalMap = { }
        for i, ( vp, acci ) in enumerate ( zip ( vpos, accidentals ) ):
            y = vp * sp / 2
            mob_noteheadTemplate = getNoteheadTemplate ( noteheadType [ i ] )
            mob_notehead = mob_noteheadTemplate.copy ( )\
                .shift ( UP * y )
            if not lastFlipped and lastVpos is not None and vp - lastVpos == 1:
                mob_notehead.shift ( RIGHT * mob_noteheadTemplate.get_width ( ) )
                lastFlipped = True
            else: lastFlipped = False
            self._mob_noteheads.add ( mob_notehead )
            
            if acci is not None:
                acciGlyph = _accidentalCodepoints [ acci ]
                metrics = _musicGlyphMetrics ( acciGlyph, musicFont )
                mob_accidentalText = MusicGlyph ( acciGlyph, musicFont = musicFont, sp = sp )\
                    .shift ( UP * ( sp * vp / 2 ) )
                lmob_accidentals.append ( mob_accidentalText )
                self._accidentalMap [ i ] = mob_accidentalText
                accidentalSegs.append ( metrics [ 1: ] + ( vp / 2 ) )

            lastVpos = vp
            
        self._mob_noteheads.shift ( self.parent.getPosition ( ) )
        
        accidentalColumns = segStack ( accidentalSegs )
        buff = self.parent.acciColumnBuff
        self._mob_accidentals = StaffElement ( self.parent )
        self._mob_accidentals.add ( self._mob_noteheads )
        for column in accidentalColumns:
            mob_accidentalColumn = StaffElement ( self.parent )
            mob_accidentalColumn.add ( *( lmob_accidentals [ i ] for i in column ) )\
                .shift ( self.getPosition ( ) )
            mob_accidentalColumn.next_to ( self._mob_accidentals, LEFT, buff * sp, coor_mask = RIGHT )
            self._mob_accidentals.add ( mob_accidentalColumn )
        self._mob_accidentals.remove ( self._mob_noteheads )
        self._mob_accidentals.shift ( LEFT * ( self.parent.acciNoteheadBuff - buff ) * sp )
        self.add ( self._mob_noteheads )
        if len ( self._mob_accidentals ) > 0: self.add ( self._mob_accidentals )
    
    @property
    def mob_ledgerLines ( self ) -> StaffElement:
        return self._mob_ledgerLines
    
    @property
    def mob_noteheads ( self ) -> StaffElement:
        return self._mob_noteheads
    
    @property
    def mob_accidentals ( self ) -> StaffElement:
        return self._mob_accidentals
    
    def getNotehead ( self, idx: int = 0 ) -> Text:
        return self._mob_noteheads [ idx ]
    
    def getAccidental ( self, idx: int = 0 ) -> Text | None:
        return self._accidentalMap.get ( idx )
    
    def copyWithoutAcci ( self ) -> Self:
        mob_copy = self.copy ( )
        if mob_copy.mob_accidentals in mob_copy:
            mob_copy.remove ( mob_copy.mob_accidentals )
        return mob_copy

class Scale ( StaffElementGroup [ Chord ] ):
    def __init__ ( 
        self, parent, 
        vpos: Iterable [ int ],
        buff: float | Iterable [ float ] = 2,
        noteheadType: str | Iterable [ str ] = "black",
        accidentals: None | Iterable [ int | None ] = None,
        ledgerLineLength: float | tuple [ float, float ] | None = 1/3,
        accidentalSpaceRatio: float = 0.5,
        **kwargs 
    ):
        super ( ).__init__ ( parent, **kwargs )
        
        if isinstance ( noteheadType, str ):
            noteheadType = it.repeat ( noteheadType )
        if not isinstance ( buff, Iterable ):
            buff = it.repeat ( buff )
            
        if accidentals is None:
            accidentals = it.repeat ( None )
        lastTarget = None
        for vp, nh, acci, b in zip ( vpos, noteheadType, accidentals, it.chain ( ( 0, ), buff ) ):
            mob_note = self.parent.createNote (
                vpos = vp, 
                noteheadType = nh, 
                ledgerLineLength = ledgerLineLength, 
                accidental = acci, 
                add = False,
            )
            if lastTarget is not None:
                mob_note.setHpos ( 
                    lastTarget.getHpos ( ) + b +
                    mob_note.mob_noteheads.getHspan ( ) + 
                    accidentalSpaceRatio * mob_note.mob_accidentals.getHspan ( )
                )
            self.add ( mob_note )
            lastTarget = mob_note
    
    def copyWithoutAcci ( self ) -> Self:
        newScale = self.copy ( )
        l = len ( newScale )
        for i in range ( l ):
            mob_note: Chord = newScale [ 0 ]
            newScale.remove ( mob_note )
            newScale.add ( mob_note.copyWithoutAcci ( ) )
        return newScale

class Staff ( VGroup, PositionedMobject ):
    """
    A five-line staff on which to display simple music content.
    """
    
    def __init__( 
            self,
            staffHeight: float = 0.7,
            staffLength: float = 24,
            staffLineThickness = 3,
            musicFont: str = "Bravura",
            changeClefScale: float = 0.8,
            keySigAcciAdvance: float = 1,
            acciColumnBuff: float = 0.25,
            acciNoteheadBuff: float = 0.5,
            ledgerLineThickness: float = 3.5,
            barlineThickness: float = 2.5,
            barlineDashLength: tuple [ float, float ] = ( 0.4, 0.4 ),
            doubleBarlineDistance: float = 0.5,
            **kwargs 
    ):
        super ( ).__init__ ( **kwargs )
        
        self._staffHeight = staffHeight
        sp = self._sp = staffHeight / 4
        self._musicFont = musicFont
        self._musicFontSize = musicFontSize = 72 * staffHeight
        self._changeClefScale = changeClefScale
        self._keySigAcciAdvance = keySigAcciAdvance
        self._acciColumnBuff = acciColumnBuff
        self._acciNoteheadBuff = acciNoteheadBuff
        self._ledgerLineThickness = ledgerLineThickness
        self._barlineThickness = barlineThickness
        self._barlineDashLength = barlineDashLength
        self._doubleBarlineDistance = doubleBarlineDistance
        
        self._mob_staffLines = VGroup ( )
        
        self._mob_sharpTemplate = Text (
            "\ue262",
            font = musicFont,
            font_size = musicFontSize,
        ).shift ( UP * ( sp * _musicGlyphMetrics ( "\ue262", musicFont ) [ 0 ] ) )
        self._mob_flatTemplate = Text (
            "\ue260",
            font = musicFont,
            font_size = musicFontSize,
        ).shift ( UP * ( sp * _musicGlyphMetrics ( "\ue260", musicFont ) [ 0 ] ) )
        
        self._mob_startingPoint = Dot ( radius = 0.01 )
        for i in range ( -2, 3 ):
            y = sp * i
            self._mob_staffLines.add (
                Line ( 
                    ( 0, y, 0 ),
                    ( staffLength * sp, y, 0 ),
                    stroke_width = staffLineThickness,
                )
            )
        self._mob_staffLines.add ( self._mob_startingPoint )
        self.add ( self._mob_staffLines )
    
    def createClef ( self, *args, add: bool = True, **kwargs ) -> Clef:
        mob_clef = Clef ( self, *args, **kwargs )
        if add: self.add ( mob_clef )
        return mob_clef

    def createKeySig ( self, *args, add: bool = True, **kwargs ) -> KeySignature:
        mob_keysig = KeySignature ( self, *args, **kwargs )
        if add: self.add ( mob_keysig )
        return mob_keysig
    
    def createBarline ( self, *args, add: bool = True, **kwargs ) -> StaffElement:
        mob_barline = Barline ( self, *args, **kwargs )
        if add: self.add ( mob_barline )
        return mob_barline   
    
    def createChord ( self, *args, add: bool = True, **kwargs ) -> Chord:
        mob_chord = Chord ( self, *args, **kwargs )
        if add: self.add ( mob_chord )
        return mob_chord
    
    def createNote ( 
            self, vpos: int, 
            noteheadType: str = "black", 
            ledgerLineLength: float | tuple [ float, float ] | None = 1/3,
            accidental: None | int = None,
            add: bool = True,
    ) -> Chord:
        return self.createChord ( 
            vpos = ( vpos, ), 
            noteheadType = noteheadType, 
            ledgerLineLength = ledgerLineLength, 
            accidentals = ( accidental, ), 
            add = add,
        )
    
    def createScale ( self, *args, add: bool = True, **kwargs ) -> Scale:
        mob_scale = Scale ( self, *args, **kwargs )
        if add: self.add ( mob_scale )
        return mob_scale
    
    def getPosition ( self ):
        return self._mob_startingPoint.get_center ( )
    
    @property
    def mob_staffLines ( self ) -> VGroup:
        return self._mob_staffLines

    @property
    def sp ( self ):
        """Staff space unit of the current  `Staff` mobject."""
        return self._sp
    
    @property
    def musicFont ( self, font: str = None ) -> str:
        if font is not None:
            self._musicFont = font
        return self._musicFont
    
    @property
    def changeClefScale ( self ) -> float:
        return self._changeClefScale   
    
    @property
    def ledgerLineThickness ( self ) -> float:
        return self._ledgerLineThickness
    
    @property
    def keySigAcciAdvance ( self ) -> float:
        return self._keySigAcciAdvance
    
    @property
    def acciColumnBuff ( self ) -> float:
        return self._acciColumnBuff
    
    @property
    def acciNoteheadBuff ( self ) -> float:
        return self._acciNoteheadBuff
    
    @property
    def barlineThickness ( self ) -> float:
        return self._barlineThickness
    
    @property
    def barlineDashLength ( self ) -> tuple [ float, float ]:
        return self._barlineDashLength
    
    @property
    def doubleBarlineDistance ( self ) -> float:
        return self._doubleBarlineDistance

