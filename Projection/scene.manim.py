from manim import *
import numpy as np

SQRT_2 = np.sqrt ( 2 )

def project ( p ): return p / p [ 2 ]

class ProjectionScene ( ThreeDScene ):
    def construct ( self ):
        self.set_camera_orientation ( phi = 50 * DEGREES, theta = 30 * DEGREES )
        
        matrices = (
            np.array ((
                ( SQRT_2, 0, 0 ),
                ( 0, SQRT_2, 0 ),
                ( SQRT_2 / 4, SQRT_2 / 4, SQRT_2 ),
            )),
        )
        
        matrix = matrices [ 0 ]
        planeExtent = ( -3, 3, -3, 3 )
        x1, x2, y1, y2 = planeExtent
        
        mob_uvecX = Arrow3D ( ORIGIN, RIGHT )
        mob_uvecY = Arrow3D ( ORIGIN, UP )
        mob_uvecZ = Arrow3D ( ORIGIN, OUT )
        mob_textX = MathTex ( "x" ).next_to ( mob_uvecX, RIGHT )
        mob_textY = MathTex ( "y" ).next_to ( mob_uvecY, UP )
        mob_textZ = MathTex ( "z" ).next_to ( mob_uvecZ, OUT )
        
        mob_center = Dot ( ORIGIN, radius = 0.06 )
        mob_plane = Polygon ( 
            ( x1, y1, 0 ), 
            ( x2, y1, 0 ), 
            ( x2, y2, 0 ), 
            ( x1, y2, 0 ), 
            color = BLUE_D,
            fill_color = BLUE_D,
            fill_opacity = 0.2,
        )
        
        mob_circle = Circle ( radius = 1, color = RED )\
            .shift ( OUT )
        
        # self.begin_ambient_camera_rotation ( rate = 0.5 )
        self.play ( 
            Create ( mob_plane ), 
            FadeIn ( mob_center ),
            run_time = 1,
        )
        self.play ( 
            Create ( mob_uvecX ),
            Create ( mob_uvecY ),
            Create ( mob_uvecZ ),
            FadeIn ( mob_textX, mob_textY, mob_textZ ),
            mob_plane.animate.shift ( OUT ),
            mob_center.animate.shift ( OUT ),
            run_time = 1,
        )
        self.play (
            Create ( mob_circle ),
            run_time = 0.5,
        )
        
        mob_transformedPlane = mob_plane.copy ( )
        mob_transformedCenter = mob_center.copy ( )
        mob_transformedUvecX = mob_uvecX.copy ( )
        mob_transformedUvecY = mob_uvecY.copy ( )
        mob_transformedUvecZ = mob_uvecZ.copy ( )
        mob_transformedUvecs = VGroup ( 
            mob_transformedUvecX, 
            mob_transformedUvecY, 
            mob_transformedUvecZ 
        )
        
        self.add ( mob_transformedUvecs )
        self.play (
            VGroup ( 
                mob_transformedPlane, 
                mob_transformedCenter, 
                mob_circle 
            ).animate.apply_matrix ( matrix ),
            ( 
                mob_uvec.animate.become ( 
                    Arrow3D ( ORIGIN, transformedBasis )
                ) 
                for mob_uvec, transformedBasis in 
                zip ( mob_transformedUvecs, matrix.T ) 
            ),
            run_time = 1.5,
        )
        
        def getPosition ( t ):
            position = np.array ((
                np.cos ( t ),
                np.sin ( t ),
                1,
            ))
            position = ( matrix @ position.T ).flatten ( )
            return position
        
        def update_pointOnCircle ( mob: Dot ):
            t = var_t.get_value ( )
            position = getPosition ( t )
            mob.move_to ( position )
        
        def update_pointOnProjection ( mob: Dot ):
            t = var_t.get_value ( )
            position = getPosition ( t )
            mob.move_to ( project ( position ) )
        
        def update_segToOrigin ( mob: Line ):
            t = var_t.get_value ( )
            position = getPosition ( t )
            mob.put_start_and_end_on ( ORIGIN, position )
        
        var_t = ValueTracker ( 0 )
        mob_pointOnCircle = Dot ( ( 1, 0, 1 ), radius = 0.06 ).apply_matrix ( matrix )
        mob_pointOnProjection = Dot ( ( 1, 0, 1 ), radius = 0.1 )  
        mob_segToOrigin = Line ( ORIGIN, mob_pointOnCircle.get_center ( ) )
        mob_transformedCircle = mob_circle.copy ( ).apply_function ( project )
        
        mob_pointOnCircle.add_updater ( update_pointOnCircle )
        mob_pointOnProjection.add_updater ( update_pointOnProjection )
        mob_segToOrigin.add_updater ( update_segToOrigin )
        
        self.play (
            FadeIn ( mob_pointOnCircle, mob_pointOnProjection ),
            Create ( mob_segToOrigin ),
            run_time = 0.5,
        )
        
        self.play (
            var_t.animate.set_value ( TAU ),
            Create ( mob_transformedCircle ),
            run_time = 1.5,
        )
        self.play (
            Uncreate ( mob_segToOrigin ),
            FadeOut ( mob_pointOnCircle, mob_pointOnProjection ),
            run_time = 0.5,
        )
        
        self.wait ( 5 )