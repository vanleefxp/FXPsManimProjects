from manim import *
import numpy as np
from numpy.typing import NDArray
from bezier import Curve as BezierCurve
import random

arr = np.array

random.seed ( 114514 )

def calcPoints ( t: float, points: NDArray, result: NDArray | None = None ):
    numPoints, dimension = points.shape
    if result is None: 
        result = np.empty ( ( numPoints - 1, dimension ) )
    start, end = None, points [ 0 ]
    for i in range ( numPoints - 1 ):
        start, end = end, points [ i + 1 ]
        result [ i ] = start * ( 1 - t ) + end * t
    return result

def randomTurbulence ( max_radius ):
    radius = random.random ( ) * max_radius
    angle = random.random ( ) * TAU
    return np.array ( ( 
        radius * np.cos ( angle ), 
        radius * np.sin ( angle ), 0 
    ) )

# make `BezierCurve` objects callable
# the return result is a 1d array representing a point on the curve at position `t`
BezierCurve.__call__ = lambda self, t: self.evaluate ( t ).transpose ( ) [ 0 ]

def makeCurve ( controlPoints: NDArray ):
    return BezierCurve ( 
        controlPoints.transpose ( ),
        len ( controlPoints ) - 1,
    )

def createControlPointsMob ( controlPoints ):
    mob_controlPoints = VGroup ( )
    mob_polyline = VGroup ( )
    for point in controlPoints: mob_controlPoints.add ( Dot ( point ) )
    start, end = None, controlPoints [ 0 ]
    for i in range ( len ( controlPoints ) - 1 ):
        start, end = end, controlPoints [ i + 1 ]
        mob_polyline.add ( Line ( start, end ).set_stroke ( opacity = 0.75 ) )
    return mob_controlPoints, mob_polyline

class BezierScene ( Scene ):
    def construct ( self ):
        controlPoints = np.array ( ( 
            ( -4, -2, 0 ), 
            ( -3, 1, 0 ),
            ( 2, 2, 0 ), 
            ( 5, -2, 0 ),
        ) )
        curve_degree = len ( controlPoints ) - 1
        
        # max_turb_radius = 0.05
        # add random turbulence to the points
        # for i in range ( curve_degree ):
        #     controlPoints [ i ] = controlPoints [ i ] + randomTurbulence ( max_turb_radius )

        curve = makeCurve ( controlPoints )
        animate_config = {
            "run_time": 5,
            "rate_func": rate_functions.ease_in_out_quad
        }

        auxControlPoints = [ controlPoints ]
        for i in range ( curve_degree ):
            auxControlPoints.append ( np.empty ( ( curve_degree - i, 3 ) ) )

        mob_curve = ParametricFunction ( curve, color = RED )
        mob_controlPoints, mob_polyline = createControlPointsMob ( controlPoints )
        mob_t_text = Variable ( 0, "t" ).to_corner ( UL )
        mob_t = mob_t_text.tracker
        mob_trace_point = Dot ( )

        def updater ( _ ):
            for i in range ( curve_degree ):
                t = mob_t.get_value ( )
                auxControlPoints [ i + 1 ] = calcPoints ( 
                    t, auxControlPoints [ i ], 
                    auxControlPoints [ i + 1 ] 
                )
        
        def getPointUpdater ( i, j ):
            return lambda mob: mob.move_to ( 
                auxControlPoints [ i + 1 ] [ j ] 
            ) 
        
        def getLineUpdater ( i, j ):
            return lambda mob: mob.put_start_and_end_on (
                auxControlPoints [ i + 1 ] [ j ], 
                auxControlPoints [ i + 1 ] [ j + 1 ]  
            )

        for i in range ( curve_degree - 1 ): 
            for j in range ( curve_degree - i ):
                mob_point = Dot ( radius = 0.06 )
                mob_point.add_updater ( getPointUpdater ( i, j ) )
                self.add ( mob_point )
            for j in range ( curve_degree - i - 1 ):
                mob_line = Line ( ).set_stroke ( opacity = 0.5 )
                mob_line.add_updater ( getLineUpdater ( i, j ) )
                self.add ( mob_line )
        
        mob_trace_point.add_updater ( lambda mob: mob.move_to ( curve ( mob_t.get_value ( ) ) ) )
        mob_t.add_updater ( updater )
        
        self.add ( mob_t_text, mob_controlPoints, mob_polyline, mob_trace_point )
        self.play ( 
            mob_t.animate ( **animate_config ).set_value ( 1 ),
            Create ( mob_curve, **animate_config ) 
        )
        self.wait ( 2 )
        self.play ( 
            mob_t.animate ( **animate_config ).set_value ( 0 ),
            Uncreate ( mob_curve, **animate_config ) 
        )
        self.wait ( 2 )
    