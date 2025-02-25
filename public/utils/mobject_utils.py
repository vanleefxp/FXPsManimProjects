from collections.abc import Callable

from manim import *
from manim.typing import Point3D

from .geometry_utils import coordSystemConverter, P

def rectByCorners ( p1: Point3D, p2: Point3D, **kwargs ) -> Rectangle:
    x1, y1 = p1 [ :2 ]
    x2, y2 = p2 [ :2 ]
    return Rectangle ( 
        width = abs ( x2 - x1 ), 
        height = abs ( y2 - y1 ), 
        **kwargs 
    ).move_to ( ( 
        ( x1 + x2 ) / 2, 
        ( y1 + y2 ) / 2, 
        0 
    ) )

def reshapeToCorners ( mob: Mobject, p1: Point3D, p2: Point3D ) -> Mobject:
    x1, y1 = p1 [ :2 ]
    x2, y2 = p2 [ :2 ]
    w, h = abs ( x2 - x1 ), abs ( y2 - y1 )
    xm, ym = ( x1 + x2 ) / 2, ( y1 + y2 ) / 2
    mob.stretch_to_fit_width ( w )\
        .stretch_to_fit_height ( h )\
        .move_to ( ( xm, ym, 0 ) )
    return mob

def plotInBox ( 
        fn: Callable [ [ float ], float ], 
        box: Rectangle | tuple [ Point3D, Point3D ],
        xRange: tuple [ float, float ] = ( 0, 1 ),
        yRange: tuple [ float, float ] = ( 0, 1 ),
        color: ParsableManimColor = RED,
        **kwargs
) -> FunctionGraph:
    if isinstance ( box, Mobject ):
        boxBottomLeft = box.get_critical_point ( DL ) [ :2 ]
        boxTopRight = box.get_critical_point ( UR ) [ :2 ]
    else:
        boxBottomLeft, boxTopRight = box

    cvt = coordSystemConverter ( 
        ( xRange, yRange ),
        np.array ( ( boxBottomLeft, boxTopRight ) ).T,
    )
    
    mob_graph = ParametricFunction (
        lambda t: P ( *cvt.src2dst ( t, fn ( t ) ) ),
        t_range = xRange,
        color = color,    
        **kwargs,
    )
    
    return mob_graph