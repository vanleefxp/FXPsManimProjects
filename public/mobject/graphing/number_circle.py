from collections.abc import Callable
import itertools as it

from manim import *
from ...utils.geometry_utils import udvec # type:ignore
from ...text_config import latexConfig

__all___ = [ "NumberCircle" ]

CCW = 1
CW = -1
OUTSIDE = 1
INSIDE = -1

class NumberCircle ( Arc ):
    def __init__ (
        self,
        radius = 2.5,
        color = WHITE,
        strokeWidth = 2,
        startAngle = PI / 2,
        angle: float = TAU,
        direction: int = CW,
        maxVal = 1,
    ):
        maxVal = abs ( maxVal )
        direction = CCW if direction >= 0 else CW
        super ( ).__init__ (
            radius = radius,
            color = color,
            angle = angle,
            stroke_width = strokeWidth,
        )
        self._mob_centerDot = Dot ( radius = 0.01 )\
            .set_fill ( opacity = 0 )\
            .set_stroke ( width = 0 )\
            .move_to ( super ( ).get_center ( ) )
        self._maxVal = maxVal
        self._startAngle = startAngle
        self._direction = direction
        self.add ( self._mob_centerDot )
    
    def getPosition ( self ):
        return self._mob_centerDot.get_center ( )
    
    def n2a ( self, number: float ) -> float:
        if self._maxVal == 0: return self._startAngle
        return ( 
            number / self._maxVal * self.angle * self._direction + 
            self._startAngle
        )
    
    def n2v ( self, number: float ) -> float:
        return udvec ( self.n2a ( number ) )
    
    def n2p ( self, number: float ) -> np.ndarray:
        position = self.getPosition ( )
        return position + self.n2v ( number ) * self.radius

    def createTick ( 
            self, number: float, 
            size: float = 0.1,
            add: bool = True 
    ) -> Line:
        tick = Line ( 
            LEFT * size, RIGHT * size, 
            stroke_width = self.get_stroke_width ( ) 
        )   .shift ( RIGHT * self.radius )\
            .rotate ( self.n2a ( number ), about_point = ORIGIN )\
            .shift ( self.getPosition ( ) )
        if add: self.add ( tick )
        return tick
    
    def createTicks (
        self, step: float = 1,
        add: bool = True,
    ):
        ticks = VGroup ( )
        for i in it.count ( ):
            value = i * step
            if value >= self._maxVal: break
            tick = self.createTick ( value, add = False )
            ticks.add ( tick )
        if add: self.add ( ticks )
        return ticks

    def addLabel ( 
            self, number: float, label: Mobject, 
            side: int = OUTSIDE,
            buff: float = 0.1, 
            add: bool = True,
    ):
        side = OUTSIDE if side >= 0 else INSIDE
        w, h = label.get_width ( ), label.get_height ( )
        d = np.hypot ( w, h )
        label.move_to ( self.n2p ( number ) )\
            .shift ( side * ( d / 2 + buff ) * self.n2v ( number ) )
        if add: self.add ( label )
        return label

    def addLabels (
        self, step: float = 1,  
        labelGenerator: Callable [ [ float ], Mobject ] = \
            lambda x: MathTex ( str ( x ), **latexConfig ),
        add: bool = True,
        **kwargs
    ):
        labels = VGroup ( )
        for i in it.count ( ):
            value = i * step
            if value >= self._maxVal: break
            label = labelGenerator ( value )
            label = self.addLabel ( value, label, add = False, **kwargs )
            labels.add ( label )
        if add: self.add ( labels )
        return labels
    
    def createLine ( self, start: float, end: float, **kwargs ) -> Line:
        startPoint = self.n2p ( start )
        endPoint = self.n2p ( end )
        return Line ( startPoint, endPoint, **kwargs )
    
    def createArc ( 
            self, start: float, diff: float, 
            buff = 0, **kwargs 
    ) -> Arc:
        startAngle = self.n2a ( start )
        return Arc ( 
            radius = self.radius + buff, 
            start_angle = startAngle, 
            angle = diff / self._maxVal * TAU * self._direction, 
            **kwargs 
        ).shift ( self.getPosition ( ) )
