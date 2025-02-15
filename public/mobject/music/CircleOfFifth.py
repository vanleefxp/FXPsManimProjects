from typing import Self
from collections.abc import Iterable

from manim.typing import Point3D
from manim import *

from ...text_config import *
from ..emphasis.with_background import withOutlineBackground
from ...utils.number_theory_utils import loop

__all__ = [ 
    "CircleOfFifth",
    "ScaleDegreeRing",
    "CircleOfFifthSector",
    "ScaleDegreeRingSector",
]

_acciCountLayerColors = ( 
    ManimColor ( "#7d92b3" ),
    ManimColor ( "#8fa7cc" ),
)
_acciCountLayerHighlightColors = (
    ManimColor ( "#b3d1ff" ),
    ManimColor ( "#a1bce6" ),
)
_acciCountTextColor = WHITE
_acciCountTextHighlightColor = WHITE

_noteNameLayerColors = (
    ManimColor ( "#c08fcc" ),
    ManimColor ( "#a87db3" ),
)
_noteNameLayerHighlightColors = (
    ManimColor ( "#d8a1d6" ),
    ManimColor ( "#f0b3ff" ),
)
_noteNameTextColor = ManimColor ( "#302433" )
_noteNameTextHighlightColor = BLACK

_toneLayerColors = (
    ManimColor ( "#b486bf" ),
    ManimColor ( "#9c74a6" ),
)
_toneLayerHighlightColors = (
    ManimColor ( "#cc98d9" ),
    ManimColor ( "#e4aaf2" ),
)
_toneTextColor = ManimColor ( "#e1cfe6" )
_toneTextHighlightColor = WHITE

_scaleDegreeColors = (
    GRAY_D, GRAY_E,
)

_majorNoteNames = (
    "C",
    r"{\sh}C/{\fl}D",
    "D",
    r"{\sh}D/{\fl}E",
    "E",
    "F",
    r"{\sh}F/{\fl}G",
    "G",
    r"{\sh}G/{\fl}A",
    "A",
    r"{\sh}A/{\fl}B",
    "B",
)
_acciCounts = (
    0,
    ( 7, -5 ),
    2,
    -3,
    4,
    -1,
    ( 6, -6 ),
    1,
    -4,
    3,
    -2,
    ( 5, -7 )
)

_co5ScaleDegrees = np.arange ( -1, 6 ) * 4 % 7
_co5ScaleDegreeArgs = np.argsort ( _co5ScaleDegrees )

def _getAcciCountText ( tonal: int ) -> str:
    acciCount = _acciCounts [ tonal ]
    if isinstance ( acciCount, int ):
        if acciCount == 0: return r"0{\sh}/0{\fl}"
        elif acciCount > 0: return rf"{acciCount}{{\sh}}"
        else: return rf"{-acciCount}{{\fl}}"
    else:
        sharps, flats = acciCount
        flats = abs ( flats )
        return rf"{sharps}{{\sh}}/{flats}{{\fl}}"

class CircleOfFifthSector ( VGroup ):
    def __init__ ( 
            self, parent: "CircleOfFifth", 
            idx: int,
            **kwargs 
    ):
        self._parent = parent
        super ( ).__init__ ( **kwargs )
        
        self._idx = i = idx
        self._highlighting = False
        
        r, r1, r2, r3 = parent.radius, parent.r1, parent.r2, parent.r3
        h1, h2, h3 = parent.h1, parent.h2, parent.h3
        
        tone = self._tone = i * 7 % 12
        accidentalCount = _getAcciCountText ( tone )
        noteName = _majorNoteNames [ tone ]
        
        mob_acciCount = VGroup ( )
        mob_major = VGroup ( )
        mob_tone = VGroup ( )
        self.add ( mob_acciCount, mob_major, mob_tone )
        
        self._mob_acciCountText = Tex ( accidentalCount, **latexConfig )\
            .shift ( ( 0, r1 + h1 / 2, 0 ) )\
            .rotate ( -PI * i / 6, about_point = ORIGIN )\
            .set_z_index ( 1 )
        self._mob_noteNameText = Tex ( noteName, **latexConfig )\
            .shift ( ( 0, r2 + h2 / 2, 0 ) )\
            .rotate ( -PI * i / 6, about_point = ORIGIN )\
            .set_z_index ( 1 )
        self._mob_toneText = MathTex ( fr"\overline{{{ i * 7 % 12 }}}", **latexConfig )\
            .shift ( ( 0, r3 + h3 / 2, 0 ) )\
            .rotate ( -PI * i / 6, about_point = ORIGIN )\
            .set_z_index ( 1 )
        
        startAngle = -i * PI / 6 + 5 * PI / 12
        self._mob_acciCountBg = AnnularSector (
            inner_radius = r1, outer_radius = r,
            angle = PI / 6,
            start_angle = startAngle,
            fill_opacity = 1,
        ).set_stroke ( width = 2, color = WHITE )
        self._mob_noteNameBg = AnnularSector (
            inner_radius = r2, outer_radius = r1,
            angle = PI / 6,
            start_angle = startAngle,
            fill_opacity = 1,
        )
        self._mob_toneBg = AnnularSector (
            inner_radius = r3, outer_radius = r2,
            angle = PI / 6,
            start_angle = startAngle,
            fill_opacity = 1,
        )
        
        mob_backgroundLayer = VGroup (
            self._mob_acciCountBg,
            self._mob_noteNameBg,
            self._mob_toneBg,
        )
        mob_foregroundLayer = VGroup (
            self._mob_acciCountText,
            self._mob_noteNameText,
            self._mob_toneText,
        )
        self.add ( mob_backgroundLayer, mob_foregroundLayer )
        self.unhighlight ( )
    
    @property
    def tone ( self ) -> int: return self._tone
    @property
    def idx ( self ) -> int: return self._idx
    @property
    def highlighting ( self ) -> bool: return self._highlighting
    
    @property
    def mob_acciCountText ( self ) -> Tex: return self._mob_acciCountText
    @property
    def mob_noteNameText ( self ) -> Tex: return self._mob_noteNameText
    @property
    def mob_toneText ( self ) -> MathTex: return self._mob_toneText   
    @property
    def mob_acciCountBg ( self ) -> AnnularSector: return self._mob_acciCountBg
    @property
    def mob_noteNameBg ( self ) -> AnnularSector: return self._mob_noteNameBg
    @property
    def mob_toneBg ( self ) -> AnnularSector: return self._mob_toneBg
    
    def highlight ( self ) -> Self:
        self.mob_acciCountBg.set_fill ( color = loop ( _acciCountLayerHighlightColors, self.idx ) )
        self.mob_noteNameBg.set_fill ( color = loop ( _noteNameLayerHighlightColors, self.idx ) )
        self.mob_toneBg.set_fill ( color = loop ( _toneLayerHighlightColors, self.idx ) )
        self.mob_acciCountText.set_color ( _acciCountTextHighlightColor )
        self.mob_noteNameText.set_color ( _noteNameTextHighlightColor )
        self.mob_toneText.set_color ( _toneTextHighlightColor )
        self._highlighting = True
    
    def unhighlight ( self ) -> Self:
        self.mob_acciCountBg.set_fill ( color = loop ( _acciCountLayerColors, self.idx ) )
        self.mob_noteNameBg.set_fill ( color = loop ( _noteNameLayerColors, self.idx ) )
        self.mob_toneBg.set_fill ( color = loop ( _toneLayerColors, self.idx ) )
        self.mob_acciCountText.set_color ( _acciCountTextColor )
        self.mob_noteNameText.set_color ( _noteNameTextColor )
        self.mob_toneText.set_color ( _toneTextColor )
        self._highlighting = False
    
    def animateHighlight ( self, **kwargs ) -> Animation:
        return AnimationGroup (
            *(
                
                mob.animate ( **kwargs ).set_fill ( color = color )
                for mob, color in (
                    ( self.mob_acciCountBg, _acciCountLayerHighlightColors ),
                    ( self.mob_noteNameBg, _noteNameLayerHighlightColors ),
                    ( self.mob_toneBg, _toneLayerHighlightColors ),
                )
            ),
        )
    
    def animateUnhighlight ( self, **kwargs ) -> Animation:
        return AnimationGroup (
            *(
                mob.animate ( **kwargs ).set_fill ( color = color )
                for mob, color in (
                    ( self.mob_acciCountBg, loop ( _acciCountLayerColors, self.idx ) ),
                    ( self.mob_noteNameBg, loop ( _noteNameLayerColors, self.idx ) ),
                    ( self.mob_toneBg, loop ( _toneLayerColors, self.idx ) ),
                )
            ),
        )

class ScaleDegreeRingSector ( VGroup ):
    def __init__ ( self, parent: "ScaleDegreeRing", i: int, **kwargs ):
        self._parent = parent
        super ( ).__init__ ( **kwargs )
        
        radius, layerThickness = parent.radius, parent.layerThickness
        
        self._position = j = i - 1
        angle = -PI * j / 6
        self._scaleDegree = scaleDegree = j * 4 % 7 + 1
        mob_arc = AnnularSector (
            inner_radius = radius - layerThickness,
            outer_radius = radius,
            start_angle = angle + 5 * PI / 12,
            angle = PI / 6,
            color = loop ( _scaleDegreeColors, j )
        ).set_stroke ( width = 2, color = WHITE, opacity = 0.5 )
        self._mob_text = withOutlineBackground (
            MathTex ( 
                f"\\hat{{{scaleDegree}}}", 
                **latexConfig,
            ) 
        )   .shift ( UP * ( radius - layerThickness / 2 ) )\
            .rotate ( angle, about_point = ORIGIN )
        self.add ( mob_arc, self._mob_text )
    
    @property
    def position ( self ) -> int: return self._position
    @property
    def scaleDegree ( self ) -> int: return self._scaleDegree
    @property
    def mob_text ( self ) -> MathTex: return self._mob_text

class ScaleDegreeRing ( VGroup ):
    def __init__ ( 
            self, 
            radius = 2, 
            layerThickness = 1, 
            **kwargs 
    ):
        self._radius = radius
        self._layerThickness = layerThickness
        super ( ).__init__ ( **kwargs )
        self._mob_center = Dot ( ORIGIN, radius = 0.01 )\
            .set_stroke ( width = 0 )\
            .set_fill ( opacity = 0 )
        self._mob_main = VGroup ( )
        self.add ( self._mob_center, self._mob_main )
        for i in range ( 7 ):
            mob_sector = ScaleDegreeRingSector ( self, i )
            self._mob_main.add ( mob_sector )
    
    @property
    def radius ( self ) -> float: return self._radius
    @property
    def layerThickness ( self ) -> float: return self._layerThickness
    
    def getPosition ( self ) -> Point3D:
        return self._mob_center.get_center ( ) 
    
    def setPosition ( self, position: Point3D ) -> Self:
        self.shift ( position - self.getPosition ( ) )
        return self
    
    def getSector ( self, position: int ) -> ScaleDegreeRingSector:
        return self._mob_main [ position ]
    
    def getSectorByDegree ( self, degree: int ) -> ScaleDegreeRingSector:
        return self.getSector ( _co5ScaleDegreeArgs [ degree ] )

class CircleOfFifth ( VGroup ):
    def __init__ ( 
        self, 
        radius = 3.25,
        layerThicknesses: tuple [ float, float, float ] = ( 0.5, 0.6, 0.6 ),
        **kwargs 
    ):
        super ( ).__init__ ( **kwargs )
        r, ( h1, h2, h3 ) = radius, layerThicknesses
        self._radius = r
        self._h1, self._h2, self._h3 = h1, h2, h3
        r1 = self._r1 = r - h1
        r2 =  self._r2 = r1 - h2
        self._r3 = r2 - h3
        
        self._var_rotation = ValueTracker ( 0 )
        self._var_rotation.is_introducer = False
        
        # an invisible point serving as the circle center indicator
        self._mob_center = Dot ( ORIGIN, radius = 0.01 )\
            .set_stroke ( width = 0 )\
            .set_fill ( opacity = 0 )
        
        # an invisible arc serving as a rotation angle indicator
        self._mob_referenceArc = Arc ( 
            radius = r, 
            start_angle = -PI / 2,
            angle = PI / 2,
        ).set_stroke ( width = 0, opacity = 0 )
        
        self._mob_main = VGroup ( )
        
        for i in range ( 12 ):
            mob_sector = CircleOfFifthSector ( self, i )
            self._mob_main.add ( mob_sector )
        
        self.add ( self._mob_center, self._mob_referenceArc, self._mob_main )
        def updateRotation ( mob: "CircleOfFifth" ):
            angle = mob._var_rotation.get_value ( )
            currentAngle = mob._mob_referenceArc.stop_angle ( )
            diff = angle - currentAngle
            mob.rotate ( diff, about_point = mob.getPosition ( ) )
        self.add_updater ( updateRotation )
    
    @property
    def radius ( self ): return self._radius
    @property
    def r1 ( self ) -> float: return self._r1
    @property
    def r2 ( self ) -> float: return self._r2
    @property
    def r3 ( self ) -> float: return self._r3
    @property
    def h1 ( self ) -> float: return self._h1
    @property
    def h2 ( self ) -> float: return self._h2
    @property
    def h3 ( self ) -> float: return self._h3

    def getPosition ( self ) -> Point3D:
        return self._mob_center.get_center ( ) 
    
    def setPosition ( self, position: Point3D ) -> Self:
        self.shift ( position - self.getPosition ( ) )
    
    @property
    def var_rotation ( self ) -> ValueTracker:
        return self._var_rotation
    
    def getRotation ( self ) -> float:
        return self._var_rotation.get_value ( )
    
    def rotateToPosition ( self, i: int ) -> "CircleOfFifth":
        self._var_rotation.set_value ( i * PI / 6 )
        return self
    
    def rotateToTone ( self, tone: int ) -> "CircleOfFifth":
        position = tone * 7 % 12
        self.rotateToPosition ( position )
        return self
    
    def animateRotateToIdx ( self, i: int, **kwargs ) -> Animation:
        angle = self._var_rotation.get_value ( )
        targetAngle = i * PI / 6
        diff = ( targetAngle - angle ) % TAU
        if diff > PI:
            diff -= TAU
        anim: Animation = self._var_rotation.animate ( **kwargs )\
            .increment_value ( diff )
        return anim

    def animateRotateToTone ( self, tone: int, **kwargs ) -> Animation:
        position = tone * 7 % 12
        return self.animateRotateToIdx ( position, **kwargs )
    
    def createScaleDegreeRing ( 
            self, addPositionUpdater = False, 
            **kwargs,
    ) -> ScaleDegreeRing:
        mob_scaleDegreeRing = ScaleDegreeRing ( radius = self.r3, **kwargs )\
            .shift ( self.getPosition ( ) )
        if addPositionUpdater:
            mob_scaleDegreeRing.add_updater ( 
                lambda mob: mob.setPosition ( self.getPosition ( ) )
            )
        return mob_scaleDegreeRing
    
    def getSector ( self, idx: int ) -> CircleOfFifthSector:
        idx %= 12
        return self._mob_main [ idx ]
    
    def sectors ( self ) -> Iterable [ CircleOfFifthSector ]:
        yield from self._mob_main
    
    def getSectorByTone ( self, tone: int ) -> CircleOfFifthSector:
        return self.getSector ( tone * 7 % 12 )
    
    def getSectorByKeyAcciAndDegree ( self, keyAcciCount: int, scaleDegree: int ) -> CircleOfFifthSector:
        idx = keyAcciCount + _co5ScaleDegreeArgs [ scaleDegree ] - 1
        return self.getSector ( idx )
    
    def sectorsByTone ( self ) -> Iterable [ CircleOfFifthSector ]:
        for tone in range ( 12 ):
            yield self.getSectorByTone ( tone )
    
    def setHighlight ( self, idx: None | int | Iterable [ int ] ) -> Self:
        if idx is None: self.clearHighlight ( )
        if isinstance ( idx, int ):
            idx %= 12
            for j in range ( 12 ):
                if j == idx: self.getSector ( j ).highlight ( )
                else: self.getSector ( j ).unhighlight ( )
        else:
            idx = frozenset ( i % 12 for i in idx )
            for j in range ( 12 ):
                if j in idx: self.getSector ( j ).highlight ( )
                else: self.getSector ( j ).unhighlight ( )
        return self
    
    def setHighlightByTone ( self, tone: int | Iterable [ int ] ) -> Self:
        if tone is None: self.clearHighlight ( )
        if isinstance ( tone, int ):
            self.setHighlight ( tone * 7 )
        else:
            self.setHighlight ( t * 7 for t in tone )
        return self
    
    def clearHighlight ( self ) -> Self:
        for sector in self._mob_main:
            sector.unhighlight ( )
        return self
