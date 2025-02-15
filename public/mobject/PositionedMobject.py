from typing import Self
from abc import ABCMeta, abstractmethod

from manim import *
from manim.typing import Point3D

class PositionedMobject ( Mobject, metaclass = ABCMeta ):
    """
    A `Mobject` with a specific point on it that represents its position.
    """
    
    @abstractmethod
    def getPosition ( self ): raise NotImplementedError
    
    def toPosition ( self, position: "Point3D | PositionedMobject" ) -> Self:
        if isinstance ( position, PositionedMobject ):
            position = position.getPosition ( )
        vec = position - self.getPosition ( )
        self.shift ( vec )
        return self