from manim import *
from manim.camera.camera import Camera
from manim.utils.rate_functions import ease_in_out_quad
import numpy as np

from functools import lru_cache
from typing import Callable

FONT = "Ysabeau Office"

def arr ( *numbers ):
    array = np.array ( numbers )
    array.setflags ( write = False )
    return array

def normal_vector ( line ):
    return line.copy ( ).rotate ( PI / 2 ).get_unit_vector ( )

@lru_cache
def circular ( t, r ) -> tuple:
    return arr (
        r * np.cos ( t ),
        r * np.sin ( t ),
        0,
    )

@lru_cache
def cycloid_on_circle ( t: float, r1: float, r2: float ) -> tuple [ float, float, float ]:
    r0, k = r1 + r2, r1 / r2
    return arr (
        np.cos ( t ) * r0 - np.cos ( ( k + 1 ) * t ) * r2,
        np.sin ( t ) * r0 - np.sin ( ( k + 1 ) * t ) * r2,
        0,
    )

@lru_cache
def cycloid_on_line ( t, r1, r2 ):
    k = r1 / r2
    return arr (
        ( t - PI ) * r1 - np.sin ( k * t ) * r2,
        -np.cos ( k * t ) * r2,
        0
    )


class CircleRotationScene ( Scene ):
    def __init__ ( 
            self, 
            show_prompt: bool = True,
            r1: float = 2, 
            r2: float = 2 / 3,
            r3: float = 0.6,
            line_extent: float = 0.35,
            animate_time: float = 6,
            easing: Callable [ [ float ], float ] = rate_functions.ease_in_out_quad,
    ):
        super ( ).__init__ ( )
        self.__show_prompt = show_prompt
        self.__r1 = r1
        self.__r2 = r2
        self.__r3 = r3
        self.__line_extent = line_extent
        self.__animate_time = animate_time
        self.__easing = easing


    def construct ( self ) -> None:
        r1 = self.__r1
        r2 = self.__r2
        r3 = self.__r3
        k = r1 / r2

        line_extent = self.__line_extent
        easing = self.__easing
        animate_time = self.__animate_time

        show_prompt = self.__show_prompt

        circle2_center = arr ( r1 + r2, 0, 0 )
        circle2_left = arr ( r1, 0, 0 )
        locus_line_start = arr ( -PI * r1, 0, 0 )
        locus_line_end = locus_line_start * ( -1, 1, 1 )
        line_start = locus_line_start - ( 0, r2, 0 )
        line_end = line_start * ( -1, 1, 1 )
        line_start_ext = line_start - ( line_extent, 0, 0 )
        line_end_ext = line_end + ( line_extent, 0, 0 )

        circle1 = Circle ( r1, color = WHITE )
        circle2 = Circle ( abs ( r2 ), color = WHITE ).move_to ( circle2_center )
        
        line1 = Line ( line_start_ext, line_end_ext )

        circle1_center_dot = Dot ( ORIGIN, radius = 0.06 )
        circle2_center_dot = Dot ( circle2_center, radius = 0.06 )
        line_start_dot = Dot ( line_start, radius = 0.06 )
        line_end_dot = Dot ( line_end, radius = 0.06 )
        trace_dot = Dot ( color = YELLOW, radius = 0.06 ).move_to ( circle2_left )

        circle2_group = VGroup ( circle2, circle2_center_dot )

        locus_circle = Circle ( r1 + r2, color = WHITE ) \
            .set_stroke ( opacity = 0.5 )
        locus_line = Line ( locus_line_start, locus_line_end ) \
            .set_stroke ( opacity = 0.5 )
        locus_cycloid_on_circle = ParametricFunction (
            lambda t: cycloid_on_circle ( t, r1, r2 ),
            t_range = ( 0, TAU ),
            fill_opacity = 0
        ).set_color ( RED )
        locus_cycloid_on_line = ParametricFunction (
            lambda t: cycloid_on_line ( t, r1, r2 ),
            t_range = ( 0, TAU ),
            fill_opacity = 0,
        ).set_color ( RED )

        theta = ValueTracker ( )

        circle2_radius = always_redraw (
            lambda: Line ( 
                circular ( theta.get_value ( ), r1 + r2 ),
                cycloid_on_circle ( theta.get_value ( ), r1, r2 ),
            )
        )

        if show_prompt:
            circle3 = Circle ( r3, color = WHITE ).to_corner ( )
            circle3_center = circle3.get_arc_center ( )
            circle3_h = circle3_center -  ( r3 * np.sign ( r2 ), 0, 0 )
            circle3_v = circle3_center - ( 0, r3 * np.sign ( r2 ), 0 )
            circle3_center_dot = Dot ( circle3_center, color = WHITE, radius = 0.06 )
            circle3_radius = Line ( 
                circle3_center, 
                circle3_h,
                color = WHITE,
            )
            circle3_radius_initial = circle3_radius.copy ( ).set_stroke ( opacity = 0.5 )
            turns_text = DecimalNumber (
                0,
                unit = r"\text{turns}",
                num_decimal_places = 2,
                unit_buff_per_font_unit = 0.003,
            ).next_to ( circle3, buff = 0.25 )

            circle_turns_updater = lambda mob: mob.set_value ( theta.get_value ( ) * abs ( k + 1 ) / TAU )
            line_turns_updater = lambda mob: mob.set_value ( theta.get_value ( ) * abs ( k ) / TAU )

        self.play ( 
            Create ( 
                circle1,
                run_time = 0.5,
            ), 
            FadeIn (
                circle1_center_dot,
                run_time = 0.5,
            )
        )

        tempList = [ circle2, circle2_center_dot, trace_dot, ]
        if show_prompt: tempList += [ circle3, circle3_center_dot, turns_text ]
        self.play ( FadeIn ( *tempList ), run_time = 0.25, )

        tempList = [ Create ( circle2_radius ) ]
        if show_prompt: tempList.append ( Create ( circle3_radius ) )
        self.play ( *tempList, run_time = 0.25, )

        if show_prompt: 
            self.add ( circle3_radius_initial )
            turns_text.add_updater ( circle_turns_updater )

        trace_dot_updater = lambda mob: mob.move_to ( cycloid_on_circle ( theta.get_value ( ), r1, r2 ) )
        trace_dot.add_updater ( trace_dot_updater )

        tempList = [
            theta.animate ( 
                run_time = animate_time,
                rate_func = easing,
            ).set_value ( TAU ),
            * ( Create (
                mob,
                run_time = animate_time,
                rate_func = easing,
            ) for mob in (
                locus_circle, locus_cycloid_on_circle
            ) ),
            Rotating (
                circle2_group,
                about_point = ORIGIN,
                run_time = animate_time,
                rate_func = easing,
            ),
        ]
        if show_prompt:
            tempList.append (
                Rotating (
                    circle3_radius,
                    axis = IN if r2 < 0 else OUT,
                    about_point = circle3_center,
                    radians = abs ( k + 1 ) * TAU,
                    run_time = animate_time,
                    rate_func = easing,
                ),
            )

        self.play ( *tempList )

        trace_dot.remove_updater ( trace_dot_updater )
        self.wait ( 2 )

        # demonstrate circle rolling on a line

        tempList = [ circle2_radius ]
        if show_prompt: tempList += [ circle3_radius, circle3_radius_initial ]
        self.play (
            FadeOut (
                locus_cycloid_on_circle,
                locus_circle,
                trace_dot,
            ),
            *( Uncreate ( mob ) for mob in tempList ),
            run_time = 0.25,
        )

        self.play (
            FadeOut ( circle1_center_dot ),
            Transform (
                circle1, line1,
            ),
            theta.animate.set_value ( 0 ),
            circle2.animate.move_to ( locus_line_start ),
            circle2_center_dot.animate.move_to ( locus_line_start ),
            run_time = 0.75,
        )

        trace_dot.move_to ( line_start )
        
        if show_prompt:
            for mob in ( circle3_radius, circle3_radius_initial ):
                mob.put_start_and_end_on (
                    circle3_center,
                    circle3_v
                )

        circle2_radius = always_redraw (
            lambda: Line (
                ( ( -PI + theta.get_value ( ) ) * r1, 0, 0 ),
                cycloid_on_line ( theta.get_value ( ), r1, r2 ),
            )
        )

        tempList = [ circle2_radius ]
        if show_prompt: tempList.append ( circle3_radius )
        self.play (
            FadeIn ( 
                line_start_dot, line_end_dot, 
                trace_dot
            ),
            *( Create ( mob ) for mob in tempList ),
            run_time = 0.25,
        )

        if show_prompt: 
            self.add ( circle3_radius_initial )
            turns_text.remove_updater ( circle_turns_updater )
            turns_text.add_updater ( line_turns_updater )
        
        trace_dot_updater = lambda mob: mob.move_to ( cycloid_on_line ( theta.get_value ( ), r1, r2 ) )
        trace_dot.add_updater ( trace_dot_updater )

        tempList = [
            theta.animate (
                rate_func = easing,
                run_time = animate_time,
            ).set_value ( TAU ),
            *( mob.animate ( 
                rate_func = easing,
                run_time = animate_time,
            ).move_to ( locus_line_end ) 
            for mob in ( 
                circle2, circle2_center_dot, 
            ) ),
            *( Create (
                mob,
                rate_func = easing,
                run_time = animate_time,
            ) for mob in (
                locus_cycloid_on_line, locus_line,
            ) ),
        ]
        if show_prompt:
            tempList.append (
                Rotating (
                    circle3_radius,
                    about_point = circle3_center,
                    radians = abs ( k ) * TAU,
                    axis = IN if r2 > 0 else OUT,
                    rate_func = easing, 
                    run_time = animate_time,
                ),
            )
        self.play ( *tempList )
        trace_dot.remove_updater ( trace_dot_updater )
        if show_prompt: turns_text.remove_updater ( line_turns_updater )

        self.wait ( 3 )

class CircleRotationScene_NoPrompt ( CircleRotationScene ):
    def __init__ ( self):
        super().__init__ ( 
            show_prompt = False,
            animate_time = 2.5,
        )

class CircleRotationScene_Internal ( CircleRotationScene ):
    def __init__ ( self ):
        super().__init__ ( r2 = -2 / 3 )

class CircleRotationScene_3D ( ThreeDScene ):
    def __init__ (
            self,
            r1: float = 2,
            r2: float = 2 / 3,
            r3: float = 0.6,
            create_animate_time: float = 6,
            uncreate_animate_time: float = 1,
            create_easing: Callable [ [ float ], float ] = rate_functions.ease_in_out_quad,
            uncreate_easing: Callable [ [ float ], float ] = smooth,
    ):
        super ( ).__init__ ( )
        self.__r1 = r1
        self.__r2 = r2
        self.__r3 = r3
        self.__create_animate_time = create_animate_time
        self.__uncreate_animate_time = uncreate_animate_time
        self.__create_easing = create_easing
        self.__uncreate_easing = uncreate_easing

    def construct ( self ):
        r1, r2 = self.__r1, self.__r2
        create_animate_time = self.__create_animate_time
        uncreate_animate_time = self.__uncreate_animate_time
        create_easing = self.__create_easing
        uncreate_easing = self.__uncreate_easing

        grid = PolarPlane ( ).set_stroke ( opacity = 0.5, color = WHITE )

        circle2_left = arr ( r1, 0, 0 )
        circle2_center = arr ( r1 + r2, 0, 0 )

        circle1 = Circle ( r1, color = WHITE )
        circle2 = Circle ( r2, color = WHITE ).move_to ( circle2_center )
        locus_circle = Circle ( r1 + r2, color = BLUE ).set_stroke ( opacity = 0.7 )

        circle1_center_dot = Dot ( radius = 0.06 )
        circle2_center_dot = Dot ( circle2_center, radius = 0.06 )
        trace_dot = Dot ( radius = 0.08, color = YELLOW ).move_to ( circle2_left )

        circle2_group = VGroup (
            circle2,
            circle2_center_dot,
        )

        theta = ValueTracker ( 0 )

        circle2_radius = Line ( circle2_center, circle2_left )

        locus_cycloid_on_circle_outer = ParametricFunction (
            lambda t: cycloid_on_circle ( t, r1, r2 ),
            t_range = ( 0, TAU ),
            fill_opacity = 0
        ).set_color ( RED )
        locus_cycloid_on_circle_inner = ParametricFunction (
            lambda t: cycloid_on_circle ( t, r1, -r2 ),
            t_range = ( 0, TAU ),
            fill_opacity = 0
        ).set_color ( RED )

        self.play ( 
            Create ( circle1 ), 
            FadeIn ( circle1_center_dot ),
            run_time = 0.5,
        )

        self.play (
            FadeIn ( circle2_group, trace_dot ),
            run_time = 0.5,
        )

        self.play (
            Create ( grid, run_time = 0.75 ),
            self.camera.theta_tracker.animate ( 
                run_time = 1 
            ).set_value ( PI ),
            self.camera.phi_tracker.animate ( 
                run_time = 1 
            ).set_value ( PI / 4 ),
            self.camera.focal_distance_tracker.animate ( 
                run_time = 1 
            ).set_value ( 15 ),
        )

        self.wait ( 0.5 )

        self.play (
            Create ( circle2_radius ),
            circle2.animate.set_fill ( WHITE, opacity = 0.5 ),
            run_time = 0.25,
        )

        trace_dot_updater = lambda mob: mob.move_to ( 
            cycloid_on_circle ( theta.get_value ( ), r1, r2 ) 
        )
        circle2_radius_updater = lambda mob: mob.put_start_and_end_on (
            circular ( theta.get_value ( ), r1 + r2 ),
            cycloid_on_circle ( theta.get_value ( ), r1, r2 )
        )
        trace_dot.add_updater ( trace_dot_updater )
        circle2_radius.add_updater ( circle2_radius_updater )

        self.play (
            theta.animate.set_value ( TAU ),
            self.camera.theta_tracker.animate.increment_value ( TAU ),
            self.camera.phi_tracker.animate.set_value ( PI / 5 ),
            Rotating ( circle2_group, about_point = ORIGIN ),
            Create ( locus_cycloid_on_circle_outer ),
            Create ( locus_circle ),
            rate_func = create_easing,
            run_time = create_animate_time,
        )

        self.wait ( 3 )

        self.play ( 
            circle2.animate.set_fill ( opacity = 0 ),
            run_time = 0.25,
        )
        self.play (
            theta.animate.set_value ( 0 ),
            self.camera.theta_tracker.animate.increment_value ( PI / 6 ),
            self.camera.phi_tracker.animate.set_value ( PI / 4 ),
            Rotating (
                circle2_group,
                about_point = ORIGIN,
                axis = IN,
            ),
            Uncreate ( locus_cycloid_on_circle_outer ),
            Uncreate ( locus_circle ),
            rate_func = uncreate_easing,
            run_time = uncreate_animate_time,
        )

        circle2_radius.remove_updater ( circle2_radius_updater )
        trace_dot.remove_updater ( trace_dot_updater )

        self.play (
            Rotating (
                VGroup ( 
                    circle2, 
                    circle2_center_dot, 
                    circle2_radius 
                ),
                about_point = circle2_left,
                axis = ( 0, -1, 0 ),
                radians = PI,
                run_time = 1,
            ),
            self.camera.theta_tracker.animate ( 
                run_time = 2,
            ).increment_value ( -PI / 6 ),
            rate_func = smooth,
        )

        self.play ( 
            circle2.animate.set_fill ( WHITE, opacity = 0.5 ), 
            run_time = 0.25 
        )

        trace_dot_updater = lambda mob: mob.move_to ( 
            cycloid_on_circle ( theta.get_value ( ), r1, -r2 ) 
        )
        circle2_radius_updater = lambda mob: mob.put_start_and_end_on (
            circular ( theta.get_value ( ), r1 - r2 ),
            cycloid_on_circle ( theta.get_value ( ), r1, -r2 )
        )
        trace_dot.add_updater ( trace_dot_updater )
        circle2_radius.add_updater ( circle2_radius_updater )
        locus_circle.become (
            Circle ( r1 - r2, BLUE ).set_stroke ( opacity = 0.7 )
        )

        self.play (
            theta.animate.set_value ( TAU ),
            self.camera.theta_tracker.animate.increment_value ( TAU ),
            self.camera.phi_tracker.animate.set_value ( PI / 5 ),
            Rotating ( circle2_group, about_point = ORIGIN ),
            Create ( locus_cycloid_on_circle_inner ),
            Create ( locus_circle ),
            run_time = create_animate_time,
            rate_func = create_easing,
        )

        self.wait ( 3 )

class CircleRotationScene_Analysis ( Scene ):
    def __init__ ( 
            self,
            r1: float = 1.6,
            r2: float = 0.9,
            theta0: float = PI / 5,
            create_animate_time: float = 2,
            uncreate_animate_time: float = 1,
            create_easing: Callable [ [ float ], float ] = rate_functions.ease_in_out_cubic,
            uncreate_easing: Callable [ [ float ], float ] = rate_functions.ease_in_out_back,
    ):
        super ( ).__init__ ( )
        self.__r1 = r1
        self.__r2 = r2
        self.__theta0 = theta0
        self.__create_animate_time = create_animate_time
        self.__uncreate_animate_time = uncreate_animate_time
        self.__create_easing = create_easing
        self.__uncreate_easing = uncreate_easing

    def construct ( self ):
        r1 = self.__r1
        r2 = self.__r2
        theta0 = self.__theta0
        create_animate_time = self.__create_animate_time
        uncreate_animate_time = self.__uncreate_animate_time
        create_easing = self.__create_easing
        uncreate_easing = self.__uncreate_easing

        circle1_center = arr ( -3.2, 0, 0 )
        circle2_left = circle1_center + ( r1, 0, 0 )
        circle2_center = circle2_left + ( r2, 0, 0 )
        circle2_center_final = circular ( theta0, r1 + r2 ) + circle1_center
        tangent_point_final = circular ( theta0, r1 ) + circle1_center

        circle1 = Circle ( r1, color = WHITE ).move_to ( circle1_center )
        circle2 = Circle ( r2, color = WHITE ).move_to ( circle2_center )

        circle1_center_dot = Dot ( circle1_center, radius = 0.06 )
        circle2_center_dot = Dot ( circle2_center, radius = 0.06 )
        trace_dot = Dot ( circle2_left, radius = 0.06, color = YELLOW )
        tangent_point_dot = Dot ( tangent_point_final, radius = 0.06, color = YELLOW )

        circle2_radius = Line ( circle2_center, circle2_left )
        circle2_group = VGroup ( circle2, circle2_center_dot )

        locus_cycloid_on_circle = ParametricFunction (
            lambda t: cycloid_on_circle ( t, r1, r2 ) + circle1_center,
            t_range = ( 0, TAU ),
            fill_opacity = 0
        ).set_color ( RED )
        locus_circle = Circle ( r1 + r2, color = WHITE ).move_to ( circle1_center ).set_stroke ( opacity = 0.5 )

        theta_value = ValueTracker ( 0 )

        self.play (
            Create ( circle1 ),
            FadeIn ( circle1_center_dot ),
            run_time = 0.5,
        )

        self.play (
            FadeIn ( circle2, circle2_center_dot, trace_dot ),
            run_time = 0.5,
        )

        self.play ( 
            Create ( circle2_radius ),
            run_time = 0.25,
        )

        circle2_radius_updater = lambda mob: mob.put_start_and_end_on (
            circular ( theta := theta_value.get_value ( ), r1 + r2 ) + circle1_center,
            cycloid_on_circle ( theta, r1, r2 ) + circle1_center,
        )
        trace_dot_updater = lambda mob: mob.move_to (
            cycloid_on_circle ( theta_value.get_value ( ), r1, r2 ) + circle1_center,
        )

        circle2_radius.add_updater ( circle2_radius_updater )
        trace_dot.add_updater ( trace_dot_updater )

        self.play (
            theta_value.animate.set_value ( TAU ),
            Rotating ( circle2_group, about_point = circle1_center ),
            Create ( locus_cycloid_on_circle ),
            Create ( locus_circle ),
            run_time = create_animate_time,
            rate_func = create_easing,
        )

        self.wait ( 1 )

        turn_back = TAU - theta0
        self.play (
            theta_value.animate.set_value ( theta0 ),
            Rotating ( 
                circle2_group, 
                about_point = circle1_center, 
                axis = IN,
                radians = turn_back,
            ),
            locus_cycloid_on_circle.animate (
                rate_func = rate_functions.ease_in_cubic,
            ).set_stroke ( opacity = 0.4 ),
            locus_circle.animate (
                rate_func = rate_functions.ease_in_cubic,
            ).set_stroke ( opacity = 0.6 ),
            run_time = uncreate_animate_time * turn_back / TAU,
            rate_func = uncreate_easing,
        )

        circle2_radius.remove_updater ( circle2_radius_updater )
        trace_dot.remove_updater ( trace_dot_updater )

        r1_line = LabeledLine ( 
            start = circle1_center, 
            end = tangent_point_final,
            label = "r_1",
            font_size = 40,
            frame_fill_opacity = 0.3,
        )
        r2_line = LabeledLine ( 
            start = circle2_center_final, 
            end = tangent_point_final,
            label = "r_2",
            font_size = 40,
            frame_fill_opacity = 0.3,
        )

        point_marker_displace = arr (
            0.2 * np.cos ( theta0 ),
            0.2 * np.sin ( theta0 ),
            0
        )

        point_marker_O1 = Tex ( 
            "$O_1$",
            font_size = 40,
        ).next_to ( circle1_center, -point_marker_displace )
        point_marker_O2 = Tex ( 
            "$O_2$",
            font_size = 40,
        ).next_to ( circle2_center_final, point_marker_displace )

        self.play (
            Create ( r1_line ),
            Create ( r2_line ),
            FadeIn ( tangent_point_dot ),
            *( Write ( mob ) for mob in ( 
                point_marker_O1, 
                point_marker_O2 
            ) ),
            run_time = 0.5,
        )

        arrow_length = r2 + 1
        v1_vec = normal_vector ( r2_line ) * arrow_length
        circle2_center_velocity_end = circle2_center_final - v1_vec
        tangent_point_velocity_end = tangent_point_final - v1_vec
        tangent_point_velocity_inverse_end = tangent_point_final + v1_vec

        circle2_center_velocity = Arrow ( 
            start = circle2_center_final,
            end = circle2_center_velocity_end,
            color = GREEN,
            max_tip_length_to_length_ratio = 0.2,
        )
        tangent_point_velocity = Arrow ( 
            start = tangent_point_final,
            end = tangent_point_velocity_end,
            color = GREEN,
            max_tip_length_to_length_ratio = 0.2,
        )
        tangent_point_velocity_inverse = Arrow ( 
            start = tangent_point_final,
            end = tangent_point_velocity_inverse_end,
            color = BLUE,
            max_tip_length_to_length_ratio = 0.2,
        )
        v1_label = MathTex ( "\\mathbf{v}_1" ).next_to ( 
            Point ( circle2_center_velocity_end ), 
            arr ( 0.2, 0, 0 ),
        )
        v2_label = MathTex ( "\\mathbf{v}_2" ).next_to ( 
            Point ( tangent_point_velocity_inverse_end ), 
            arr ( -0.2, 0, 0 ),
        )

        self.wait ( 1 )

        self.play ( 
            Create ( circle2_center_velocity ),
            Write ( v1_label ),
            run_time = 0.5,
        )
        self.play ( 
            Indicate ( r1_line ),
            Indicate ( r2_line ),
        )

        self.wait ( 1 )

        self.play ( Flash ( tangent_point_dot ) )

        self.play (
            Transform ( 
                temp_mob := circle2_center_velocity.copy ( ),
                tangent_point_velocity, 
            ),
            run_time = 0.5,
        )

        self.remove ( temp_mob )
        self.add ( tangent_point_velocity )

        self.wait ( 1 )

        self.play (
            Transform (
                temp_mob := tangent_point_velocity.copy ( ),
                tangent_point_velocity_inverse,
            ),
            Write ( v2_label ),
            run_time = 0.5,
        )

        self.remove ( temp_mob )
        self.add ( tangent_point_velocity_inverse )

        self.play ( Indicate ( r2_line ) )

        self.wait ( 3 )
        
