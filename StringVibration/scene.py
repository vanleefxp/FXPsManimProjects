from collections.abc import Callable
from fractions import Fraction as Q
import sys, json

from manim import *
import numpy as np
from pathlib import Path

DIR = Path ( __file__ ).parent if "__file__" in locals ( ) else Path.cwd ( )
sys.path.append ( str ( ( DIR/".." ).resolve ( ) ) )

from public.sound.waveform import *

latexTemplate = TexTemplate (
    tex_compiler = "xelatex",
    output_format = ".xdv",
    preamble = ( DIR/"assets/preamble.tex" ).read_text ( ),
)

latexConfig = {
    "font_size": 32,
    "tex_template": latexTemplate,
}
textConfig = {
    "font": "CEF Fonts CJK",
    "font_size": 25,
}
analyzeConfig = {
    "freqTolerance": 100,
    "sampleTime": 0.5,
    "harmonicThreshold": 0.05,
}

def smoothStart ( smoothRatio: float ) -> Callable [ [ float ], float ]:
    r = smoothRatio
    @rate_functions.unit_interval
    def _func ( t: float ) -> float:
        k = 1 / ( 1 - r / 2 )
        if t < r:
            return t * t * k / r / 2
        else:
            return k * ( t - r / 2 )
    return _func

def smoothEnd ( smoothRatio: float ) -> Callable [ [ float ], float ]:
    smoothStartFunc = smoothStart ( smoothRatio )
    return lambda x: 1 - smoothStartFunc ( 1 - x )

def smoothBoth ( smoothRatio: float ) -> Callable [ [ float ], float ]:
    smoothStartFunc = smoothStart ( smoothRatio )
    smoothEndFunc = smoothEnd ( smoothRatio )
    def _func ( t: float ) -> float:
        if t < 0.5:
            return smoothStartFunc ( 2 * t ) / 2
        else:
            return ( smoothEndFunc ( 2 * t - 1 ) + 1 ) / 2
    return _func

def createGlow ( vmobject, radius = 1, color = YELLOW ) -> VGroup:
    # 参考：https://www.reddit.com/r/manim/comments/xsktrb/code_for_glowing_light_effect/
    glow_group = VGroup ( vmobject )
    for idx in range ( 60 ):
        new_circle = Circle ( 
            radius = radius * ( 1.002 ** ( idx ** 2 ) ) / 400, 
            stroke_opacity = 0, 
            fill_color = color,
            fill_opacity=0.2-idx / 300
        ).move_to ( vmobject )
        glow_group.add ( new_circle )
    return glow_group 

def getCutoffLine ( p1, p2, xmin, xmax ):
    if p1 [ 0 ] > p2 [ 0 ]: 
        swapped = True
        p1, p2 = p2, p1
    else: swapped = False
    x1, y1, _ = p1
    x2, y2, _ = p2
    if x1 >= xmin and x2 <= xmax:
        if swapped: p1, p2 = p2, p1
        return True, p1, p2
    if x2 < xmin or x1 > xmax: return False, None, None
    k = ( y2 - y1 ) / ( x2 - x1 )
    b = y1 - k * x1
    if x1 < xmin: p1 = np.array (( xmin, k * xmin + b, 0 ))
    if x2 > xmax: p2 = np.array (( xmax, k * xmax + b, 0 ))
    if swapped: p1, p2 = p2, p1
    return True, p1, p2

def createBoundedParametricGraph (
    fn: Callable [ [ float ], np.ndarray [ float ] ],
    t_range: tuple [ float, float ] = ( 0, 1 ),
    x_range: tuple [ float, float ] = ( -np.inf, np.inf ),
    divisions: int = 200,
    **kwargs
) -> VGroup:
    vg = VGroup ( )
    xmin, xmax = x_range
    tmin = t_range [ 0 ]
    prevPoint = fn ( tmin )
    for t in np.linspace ( *t_range, divisions ):
        currentPoint = fn ( t )
        visible, p1, p2 = getCutoffLine ( prevPoint, currentPoint, xmin, xmax )
        if visible:
            vg.add ( Line ( p1, p2, color = PURE_GREEN ) )
        prevPoint = currentPoint
    return vg

def complexToPoint ( z: complex ) -> np.ndarray [ float ]:
    re, im = z.real, z.imag
    return np.array (( re, im, 0 ))

def findMax ( fn, divs = 1000 ):
    fn = np.vectorize ( fn )
    x = np.linspace ( 0, 1, divs )
    y = fn ( x )
    return np.max ( np.abs ( y ) )

class IntroductionScene ( Scene ):
    def construct ( self ):
        self.camera.background_color = "#282c34"
        
        mob_tex_logo = Tex ( 
            r"$\mathbb{F}[x]_p$ Presents",
            **( latexConfig | {"font_size": 144} )
        )
        mob_text_word = Text ( "波动合万象，音声辨彼此。", **( textConfig | {"font_size": 48} ) )\
            .next_to ( mob_tex_logo, DOWN, buff = 0.5 )
        mob_text_provide = Text ( "提   供", **( textConfig | {"font_size": 48} ) )\
            .to_corner ( UP, buff = 1 )
        self.add ( mob_text_provide )
        self.play (
            Write ( mob_tex_logo ),
            Write ( mob_text_word ),
            run_time = 0.5,
        )
        self.wait ( 1.5 )
        self.play (
            LaggedStart (
                FadeOut ( mob_tex_logo, mob_text_word, run_time = 0.5 ),
                FadeOut ( mob_text_provide, run_time = 0.5 ),
                lag_ratio = 0.25,
            )
        )
        
        mob_manimLogo = SVGMobject (
            DIR/"assets/image/manim-logo_transparent-background.svg"
        )
        mob_text_manim = Text ( "Animation by Manim", **( textConfig | {"font_size": 72} ) )\
            .next_to ( mob_manimLogo, LEFT, buff = 0.5 )
        VGroup ( mob_manimLogo, mob_text_manim )\
            .center ( )
        self.play (
            Succession (
                Write ( mob_text_manim, run_time = 0.5 ),
                Create ( mob_manimLogo, run_time = 0.25 ),
            )
        )
        self.wait ( 2 )
        self.play (
            FadeOut ( mob_text_manim, mob_manimLogo ),
            run_time = 1,
        )

class StandingWaveScene ( Scene ):
    def construct ( self ):
        self.camera.background_color = "#282c34"
        rx = config [ "frame_x_radius" ]
        
        waveCenterY = -1.25
        wl = 2.5
        amp = 1
        T = 2
        n_periods = 5
        
        mob_text_title = Text ( "驻波\n原理", **(textConfig | {"font_size": 84}) )\
            .to_corner ( UL ).shift ( RIGHT * 0.3 )
        
        # 第一个谐波，初相为 pi / 2 的右行波
        mob_tex_wave1 = MathTex ( 
            r"y_1(x, t) = A \cos \left(2 \pi f \left(t - \frac{x}{v}\right)\right)",
            **latexConfig,
        ).next_to ( mob_text_title, RIGHT, buff = 1 )\
            .align_to ( mob_text_title, UP )
        mob_tex_wave1Note = Tex ( 
            r"原点初相 $\frac{\pi}{2}$, 右行",
            **latexConfig,
        )   .next_to ( mob_tex_wave1, RIGHT, buff = 0.75 )
    
        # 第二个谐波，初相为 -pi / 2 的左行波
        mob_tex_wave2 = MathTex ( 
            r"y_2(x, t) = -A \cos \left(2 \pi f \left(t + \frac{x}{v}\right)\right)",
            **latexConfig,
        )   .next_to ( mob_tex_wave1, DOWN, buff = 0.25 )\
            .align_to ( mob_tex_wave1, LEFT )
        mob_tex_wave2Note = Tex ( 
            r"原点初相 $-\frac{\pi}{2}$, 左行",
            **latexConfig,
        )   .next_to ( mob_tex_wave2, RIGHT, buff = 0.75 )
        
        # 两个谐波叠加形成驻波
        mob_tex_standingWave = MathTex ( 
            r"y(x, t) = y_1 + y_2 = 2 A",
            r"\sin \left(2 \pi \frac{x}{\lambda}\right)",
            r"\sin (2 \pi ft)",
            **latexConfig,
        )\
            .next_to ( mob_tex_wave2, DOWN, buff = 0.25 )\
            .align_to ( mob_tex_wave2, LEFT )
        
        # 波速与频率、波长的关系
        mob_tex_waveSpeed = MathTex ( 
            r"v = \lambda f = \sqrt{T / \mu}",
            **latexConfig,
        )\
            .next_to ( mob_tex_standingWave, RIGHT, buff = 0.75 )
        
        def makeWaveMob ( 
                t: float, phi: float = 0, 
                color: ManimColor = BLUE 
        ) -> Mobject:
            return FunctionGraph ( 
                lambda x: amp * np.sin ( TAU * ( t / T - x / wl ) + phi ),
                color = color,
                x_range = [ -rx - wl, rx + wl ],
            ).move_to ( waveOrigin )
        
        def makeStandingWaveMob ( t: float, color: ManimColor = RED ) -> Mobject:
            return FunctionGraph (
                lambda x: 2 * amp * np.sin ( TAU * t / T ) * np.sin ( TAU * x / wl ),
                color = color,
            ).move_to ( waveOrigin )
        
        waveOrigin = np.array (( 0, waveCenterY, 0 ))
        wave1Start = waveOrigin + ( 0, amp, 0 )
        wave2Start = waveOrigin - ( 0, amp, 0 )
        antiNodeOrigin = waveOrigin + ( wl / 4, 0, 0 )
        
        mob_dot_nodeOrigin = Dot ( waveOrigin, radius = 0.06 )
        mob_dot_nodeWave1 = Dot ( wave1Start, radius = 0.06 )
        mob_dot_nodeWave2 = Dot ( wave2Start, radius = 0.06 )
        mob_dot_antiNodeOrigin = Dot ( antiNodeOrigin, radius = 0.06 )
        mob_dot_antiNodeWave = Dot ( antiNodeOrigin, radius = 0.06 )
        mob_dot_antiNodeStandingWave = Dot ( antiNodeOrigin, radius = 0.06 )
        mob_seg_nodeWave1 = Line ( waveOrigin, wave1Start )
        mob_seg_nodeWave2 = Line ( waveOrigin, wave2Start )
        mob_line_xAxis = Line ( ( -rx, waveCenterY, 0 ), ( rx, waveCenterY, 0 ) )\
            .set_stroke ( opacity = 0.5 )
        mob_var_t = ValueTracker ( )
        
        mob_curve_wave1 = makeWaveMob ( 0, PI / 2, BLUE ) 
        mob_curve_wave2 = makeWaveMob ( 0, -PI / 2, GREEN )
        
        mob_arrow_origin = Arrow ( ORIGIN, UP )\
            .next_to ( mob_dot_nodeOrigin, DOWN, buff = 0.2 )
        mob_tex_origin = MathTex ( r"x = 0", **latexConfig )\
            .next_to ( mob_arrow_origin, DOWN, buff = 0.2 )
        
        mob_curve_standingWave = always_redraw ( 
            lambda: makeStandingWaveMob ( mob_var_t.get_value ( ) ) 
        )
        
        def makeSegAntiNodeMob ( ) -> Mobject:
            t = mob_var_t.get_value ( ) % T
            return Line ( 
                antiNodeOrigin, 
                antiNodeOrigin + ( 0, 2 * amp * np.sin ( TAU * t / T ), 0 )
            )
        
        mob_seg_antiNode = always_redraw ( makeSegAntiNodeMob )
        
        self.play ( Write ( mob_text_title, run_time = 1 ) )
        self.play (
            Succession (
                Write ( mob_tex_wave1, run_time = 1 ),
                Write ( mob_tex_wave1Note, run_time = 0.5 ),
            )
        )
        
        self.play ( 
            Create ( mob_curve_wave1 ),
            Create ( mob_line_xAxis ),
            FadeIn ( 
                mob_dot_nodeOrigin, mob_dot_nodeWave1, mob_seg_nodeWave1,
                mob_dot_antiNodeOrigin, mob_dot_antiNodeWave, mob_dot_antiNodeStandingWave,
                mob_arrow_origin, mob_tex_origin,
                run_time = 0.5 
            ),
        )
        self.wait ( 1 )
        
        self.play ( 
            Succession (
                Write ( mob_tex_wave2, run_time = 1 ),
                Write ( mob_tex_wave2Note, run_time = 0.5 ),
            ),
            FadeOut ( mob_arrow_origin, mob_tex_origin, run_time = 0.5 ),
        )
        
        self.play ( 
            mob_curve_wave1.animate.set_stroke ( opacity = 0.5 ),
            Create ( mob_curve_wave2 ),
            FadeIn ( mob_dot_nodeWave2, mob_seg_nodeWave2, run_time = 0.5 ),
        )
        self.wait ( 1 )
        
        # 使用平移模拟波的传播，加快渲染
    
        def updateWave1 ( mob: Mobject ) -> None:
            t = mob_var_t.get_value ( ) % T
            mob.move_to ( waveOrigin + ( wl * t / T, 0, 0 ) )
        
        def updateNodeWave1Dot ( mob: Mobject ) -> None:
            t = mob_var_t.get_value ( ) % T
            mob.move_to ( waveOrigin + ( 0, amp * np.cos ( TAU * t / T ), 0 ) )
        
        def updateWave1Seg ( mob: Mobject ) -> None:
            t = mob_var_t.get_value ( ) % T
            mob.put_start_and_end_on ( 
                waveOrigin, 
                waveOrigin + ( 0, amp * np.cos ( TAU * t / T ), 0 ) 
            )
        
        def updateAntiNodeWaveDot ( mob: Mobject ) -> None:
            t = mob_var_t.get_value ( ) % T
            mob.move_to ( antiNodeOrigin + ( 0, amp * np.sin ( TAU * t / T ), 0 ) )
        
        def updateAntiNodeStandingWaveDot ( mob: Mobject ) -> None:
            t = mob_var_t.get_value ( ) % T
            mob.move_to ( antiNodeOrigin + ( 0, 2 * amp * np.sin ( TAU * t / T ), 0 ) )
                
        
        def updateWave2 ( mob: Mobject ) -> None:
            t = mob_var_t.get_value ( ) % T
            mob.move_to ( waveOrigin + ( -wl * t / T, 0, 0 ) )
        
        def updateWave2Seg ( mob: Mobject ) -> None:
            t = mob_var_t.get_value ( ) % T
            mob.put_start_and_end_on ( 
                waveOrigin, 
                waveOrigin +  ( 0, - amp * np.cos ( TAU * t / T ), 0 ) 
            )
        
        def updateWave2Dot ( mob: Mobject ) -> None:
            t = mob_var_t.get_value ( ) % T
            mob.move_to ( waveOrigin + ( 0, - amp * np.cos ( TAU * t / T ), 0 ) )
        
        mob_curve_wave1.add_updater ( updateWave1 )
        mob_curve_wave2.add_updater ( updateWave2 )
        mob_dot_nodeWave1.add_updater ( updateNodeWave1Dot )
        mob_dot_nodeWave2.add_updater ( updateWave2Dot )
        mob_seg_nodeWave1.add_updater ( updateWave1Seg )
        mob_seg_nodeWave2.add_updater ( updateWave2Seg )
        mob_dot_antiNodeWave.add_updater ( updateAntiNodeWaveDot )
        mob_dot_antiNodeStandingWave.add_updater ( updateAntiNodeStandingWaveDot )
        
        self.add ( mob_seg_antiNode )
        
        animateTime = T * ( n_periods + 0.25 )
        self.play (
            mob_curve_wave1.animate.set_stroke ( opacity = 0.75 ),
            mob_curve_wave2.animate.set_stroke ( opacity = 0.75 ),  
            Succession (
                Write ( mob_tex_standingWave, run_time = 1 ),
                Write ( mob_tex_waveSpeed, run_time = 0.5 ),
            ),
            Succession (
                Create ( mob_curve_standingWave ),
                mob_var_t.animate ( rate_func = smoothBoth ( 0.1 ), run_time = animateTime )\
                    .set_value ( animateTime ),
            ),
        )
        self.play (
            Uncreate ( mob_curve_wave1 ),
            Uncreate ( mob_curve_wave2 ),
            FadeOut ( 
                mob_seg_nodeWave1, mob_seg_nodeWave2, 
                mob_dot_nodeWave1, mob_dot_nodeWave2, 
                mob_dot_antiNodeWave 
            )
        )
        
        mob_tex_amp = MathTex ( r"2A", **latexConfig )\
            .next_to ( mob_seg_antiNode, RIGHT, buff = 0.2 )
        mob_seg_nodeAntiNode = Line ( waveOrigin, antiNodeOrigin )
        mob_tex_nodeAntiNode = MathTex ( r"\frac{\lambda}{4}", **latexConfig )\
            .next_to ( mob_seg_nodeAntiNode, DOWN, buff = 0.15 )
        
        mob_text_nodeNote = Text ( "波节", **textConfig )\
            .next_to ( mob_dot_nodeOrigin, UL, buff = 0.1 )
        mob_text_antiNodeNote = Text ( "波腹", **textConfig )\
            .next_to ( mob_dot_antiNodeStandingWave, LEFT, buff = 0.12 )
        
        self.play (
            Write ( mob_text_nodeNote, run_time = 1 ),
            Write ( mob_text_antiNodeNote, run_time = 1 ),
        )
        self.wait ( 1 )
        
        self.play (
            Write ( mob_tex_amp, run_time = 1 ),
            Create ( mob_seg_nodeAntiNode ),
            Write ( mob_tex_nodeAntiNode, run_time = 1 )
        )
        self.wait ( 2 )
        
class WaveReflectionScene ( Scene ):
    def construct ( self ):
        self.camera.background_color = "#282c34"
        
        stringLength = 12
        wallHeight = 2
        wl = 3.2
        amp = 1
        T = 2
        nPeriods = 15
        stringY = 0.3
        
        mob_text_title = Text ( "波反射与半波损失", **(textConfig | {"font_size": 84}) )\
            .to_corner ( UL ).shift ( RIGHT * 0.3 )
            
        mob_text_note1 = Paragraph ( 
            "于一端固定的单弦上形成的简谐波，其在反射时，反射波与入射波之间存在 π 相位",
            "的突变，称为半波损失。",
            **textConfig,
            alignment = "left",
            line_spacing = 0.8,
        ).to_corner ( DL ).shift ( ( 0.3, 0.8, 0 ) )
        
        mob_text_note2 = Paragraph (
            "反射波与入射波叠加形成驻波。",
            "半波损失的存在使得单弦的固定端始终成为波节。",
            **textConfig,
            alignment = "left",
            line_spacing = 0.8,
        ).to_corner ( DL ).shift ( ( 0.3, 0.8, 0 ) )
        
        stringRight = np.array (( stringLength / 2, stringY, 0 ))
        stringLeft = np.array (( -stringLength / 2, stringY, 0 ))
        wallUp = stringRight + UP * ( wallHeight / 2 )
        wallDown = stringRight + DOWN * ( wallHeight / 2 )
        mob_line_string = Line ( stringRight, stringLeft )\
            .set_stroke ( opacity = 0.5 )
        mob_line_wall = Line ( wallUp, wallDown )
        mob_dot_stringEnd = Dot ( stringRight, radius = 0.06 )
        mob_var_t = ValueTracker ( )
        
        runTime = T * nPeriods
        reflectionStartTime = stringLength / wl * T
        remainTime = runTime - reflectionStartTime
        
        def calcIncidenceWave ( x, t ):
            x_max = wl * t / T
            if x >= x_max: return 0
            return amp * np.sin ( TAU * ( t / T - x / wl ) )
        
        def calcReflectionWave ( x, t ):
            if t < reflectionStartTime: return 0
            t1 = t - reflectionStartTime
            x_lim = wl / T * t1
            if x >= x_lim: return 0
            return -amp * np.sin ( TAU * ( t1 / T - x / wl ) )
        
        def calcCombinedWave ( x, t ):
            return calcIncidenceWave ( x, t ) + calcReflectionWave ( stringLength - x, t )
        
        def createIncidenceWave ( t ):
            mob = FunctionGraph (
                lambda x: calcIncidenceWave ( x, t ), x_range = [ 0, stringLength ],
                color = RED if t < reflectionStartTime else BLUE,
            ).shift ( stringLeft ).reverse_direction ( )
            if t < reflectionStartTime:
                mob.set_stroke ( opacity = 0.75 )
            return mob
        
        def createReflectionWave ( t ):
            t1 = t - reflectionStartTime
            return FunctionGraph (
                lambda x: -amp * np.sin ( TAU * ( t1 / T + x / wl ) ),
                x_range = [ -min ( wl / T * t1, stringLength ), 0 ],
                color = GREEN
            ).shift ( stringRight ).set_stroke ( opacity = 0.75 )
        
        def createCombinedWave ( t ):
            return FunctionGraph (
                lambda x: calcCombinedWave ( x, t ), x_range = [ 0, stringLength ],
                color = RED,
            ).shift ( stringLeft )
        
        mob_graph_incidenceWave = always_redraw (
            lambda: createIncidenceWave ( mob_var_t.get_value ( ) )
        )
        
        self.play (
            Succession (
                Write ( mob_text_title, run_time = 1 ),
                FadeIn ( mob_line_wall, run_time = 0.5 ),
            )
        )
        self.play (
            Create ( mob_line_string, run_time = 0.5 ),
            Create ( mob_graph_incidenceWave, run_time = 1 ),
        )
        self.play ( Write ( mob_text_note1, run_time = 1 ) )
        self.play (
            mob_var_t.animate ( rate_func = linear, run_time = reflectionStartTime )\
                .set_value ( reflectionStartTime ),
            FadeIn ( mob_dot_stringEnd, run_time = 0.5 ),
        )
        
        mob_graph_reflectionWave = always_redraw (
            lambda: createReflectionWave ( mob_var_t.get_value ( ) )
        )
        mob_graph_combinedWave = always_redraw (
            lambda: createCombinedWave ( mob_var_t.get_value ( ) )
        )
        
        self.add ( mob_graph_reflectionWave, mob_graph_combinedWave )
        self.play (
            Unwrite ( mob_text_note1, run_time = 1 ),
            Write ( mob_text_note2, run_time = 1 ),
            Flash ( mob_dot_stringEnd, color = YELLOW, run_time = 1 ),
            mob_var_t.animate (  rate_func = linear, run_time = remainTime )\
                .set_value ( runTime ),
        )

class StandingWaveOnStringScene ( Scene ):
    def construct ( self ):
        self.camera.background_color = "#282c34"
        
        waveCenterY = -0.9
        stringLength = 12
        amp = 1.25
        waveOrigin = np.array (( 0, waveCenterY, 0 ))
        stringRight = np.array(( stringLength / 2, 0, 0 ))
        stringLeft = -stringRight
        mob_seg_string = Line ( 
            stringLeft, 
            stringRight
        ).shift ( waveOrigin )
        mob_dot_stringLeft = Dot ( 
            stringLeft, 
            radius = 0.06 
        ).shift ( waveOrigin )
        mob_dot_stringRight = Dot ( 
            stringRight,
            radius = 0.06 
        ).shift ( waveOrigin )
        
        l_mob_curve_waves = [ ]
        l_mob_curve_invWaves = [ ]
        for k in range ( 1, 7 ):
            wl = 2 / k * stringLength
            mob = FunctionGraph (
                lambda x: amp * np.sin ( TAU * x / wl ),
                x_range = [ 0, stringLength ],
                color = RED,
            ).shift ( waveOrigin - stringRight )
            mob_inv = FunctionGraph (
                lambda x: -amp * np.sin ( TAU * x / wl ),
                x_range = [ 0, stringLength ],
                color = RED,
            ).set_stroke ( opacity = 0.5 ) \
                .shift ( waveOrigin - stringRight )
            l_mob_curve_waves.append ( mob )
            l_mob_curve_invWaves.append ( mob_inv )
            
        mob_curve_wave = Line ( 
            stringLeft, stringRight,
            color = RED,
        ).shift ( waveOrigin )
        mob_curve_invWave = mob_curve_wave.copy ( )
        
        mob_text_title = Text ( "单弦\n驻波", **(textConfig | {"font_size": 84}) )\
            .to_corner ( UL ).shift ( RIGHT * 0.3 )
            
        mob_text_note1 = Text (
            "单弦驻波由入射波和反射波叠加形成，两端点都是波节",
            **textConfig,
        ).next_to ( mob_text_title, RIGHT, buff = 0.75 )\
            .align_to ( mob_text_title, UP )
            
        mob_tex_normalize = Tex ( 
            r"归一化条件：$A = 1 / 2$, 弦长 $L = 1$", 
            **latexConfig 
        ).next_to ( mob_text_note1, DOWN, buff = 0.25 )\
            .align_to ( mob_text_note1, LEFT )
            
        mob_tex_standingWave = MathTex ( 
            r"y(x, t) =",
            r"\sin \left(2 \pi \frac{x}{\lambda})",
            r"\sin (2 \pi ft)",
            **latexConfig 
        ).next_to ( mob_tex_normalize, DOWN, buff = 0.25 )\
            .align_to ( mob_tex_normalize, LEFT )
        mob_tex_standingWaveBoundary = MathTex ( 
            r"y(0, t) = y(1, t) \equiv 0",
            **latexConfig 
        ).next_to ( mob_tex_standingWave, RIGHT, buff = 0.5 )
        
        mob_tex_waveSegs = MathTex (
            r"2 / \lambda = k \in \mathbb{N}^{*}",
            **latexConfig
        ).next_to ( mob_tex_standingWave, DOWN, buff = 0.1 )\
            .align_to ( mob_tex_standingWave, LEFT )
        mob_tex_waveSegsNote = Tex (
            r"$k$ 称为波段数，指单弦上所容纳的半波长个数",
            **latexConfig
        ).next_to ( mob_tex_waveSegs, RIGHT, buff = 0.5 )
        
        self.play (
            Succession (
                Write ( mob_text_title, run_time = 1 ),
                Write ( mob_text_note1, run_time = 1 ),
            )
        )
        
        self.play (
            Create ( mob_seg_string, run_time = 0.5 ),
            FadeIn ( mob_dot_stringLeft, run_time = 0.5 ),
            FadeIn ( mob_dot_stringRight, run_time = 0.5 ),
        )
        self.play (
            Flash ( mob_dot_stringLeft, color = YELLOW ),
            Flash ( mob_dot_stringRight, color = YELLOW ),
        )
        self.wait ( 1 )
        
        self.play (
            Succession (
                Write ( mob_tex_normalize, run_time = 1 ),
                Wait ( 0.25 ),
                Write ( mob_tex_standingWave, run_time = 1 ),
                Wait ( 0.25 ),
                Write ( mob_tex_standingWaveBoundary, run_time = 1 ),
                Wait ( 1 ),
                Write ( mob_tex_waveSegs, run_time = 0.5 ),
                Wait ( 0.25 ),
                Write ( mob_tex_waveSegsNote, run_time = 1 ),
            )
        )
        
        # 波形大图，逐一变换
        
        mob_tex_kValue = MathTex ( r"k = 0", **latexConfig )\
            .to_corner ( DL ).shift ( UP * 0.8 )
        
        self.play ( 
            FadeIn ( mob_curve_wave, mob_curve_invWave ),
            mob_seg_string.animate.set_stroke ( opacity = 0.5 ),
            Write ( mob_tex_kValue ),
            run_time = 0.5,
        )
        for i, ( mob, mob_inv ) in enumerate ( zip ( l_mob_curve_waves, l_mob_curve_invWaves ) ):
            self.play ( 
                Transform ( mob_curve_wave, mob ),
                Transform ( mob_curve_invWave, mob_inv ),
                Transform ( 
                    mob_tex_kValue, 
                    MathTex ( f"k = {i + 1}", **latexConfig )\
                        .to_corner ( DL ).shift ( UP * 0.8 ) 
                ),
                run_time = 0.75,
            )
            self.wait ( 0.25 )
        
        # 隐藏大图，显示波形小图
        
        self.play (
            FadeOut ( 
                mob_dot_stringLeft, mob_dot_stringRight,
                mob_seg_string, 
                mob_curve_wave, mob_curve_invWave,
                mob_tex_kValue,
                run_time = 0.5,
            ),
        )
        
        diagramStringLength = 3.5
        diagramAmp = 0.6
        
        def createWaveDiagram ( k ):
            rightEnd = RIGHT * diagramStringLength
            mob_vg = VGroup ( )
            mob_line_string = Line ( ORIGIN, rightEnd )\
                .set_stroke ( opacity = 0.5 )
            mob_dot_left = Dot ( )
            mob_dot_right = Dot ( rightEnd )
            wl = 2 / k * diagramStringLength
            mob_wave = FunctionGraph (
                lambda x: diagramAmp * np.sin ( TAU * x / wl ),
                x_range = [ 0, diagramStringLength ],
                color = RED,
            )
            mob_invWave = FunctionGraph (
                lambda x: -diagramAmp * np.sin ( TAU * x / wl ),
                x_range = [ 0, diagramStringLength ],
                color = RED,
            ).set_stroke ( opacity = 0.5 )
            mob_tex_k = MathTex ( f"k = {k}", **latexConfig )\
                .next_to ( mob_line_string, DOWN, buff = 0.15 )\
                .shift ( DOWN * diagramAmp )
            mob_vg.add ( 
                mob_line_string,
                mob_dot_left, mob_dot_right,  
                mob_wave, mob_invWave,
                mob_tex_k,
            )
            return mob_vg
        
        l_mob_waveDiagrams = [ createWaveDiagram ( k ) for k in range ( 1, 7 ) ]
        VGroup ( *l_mob_waveDiagrams )\
            .arrange_in_grid ( 2, 3, buff = ( 0.5, 0.45 ) )\
            .center ( )\
            .shift ( DOWN )
        
        self.play ( *( Create ( mob ) for mob in l_mob_waveDiagrams ) )
        
        self.play (
            Transform ( 
                mob_tex_standingWave, 
                MathTex ( 
                    r"y_k(x, t) =",
                    r"\sin \left(2 \pi \frac{x}{\lambda_k})",
                    r"\sin (2 \pi f_k t)",
                    **latexConfig 
                ).next_to ( mob_text_title, RIGHT, buff = 0.75 )\
                    .align_to ( mob_text_title, UP ) 
            ),
            FadeOut ( 
                mob_tex_standingWaveBoundary, 
                mob_tex_waveSegs,
                mob_tex_waveSegsNote,
                mob_tex_normalize,
                mob_text_note1,
                run_time = 0.5 
            ),
        )
        mob_tex_wavelength = MathTex (
            r"\lambda_k = 2 / k",
            **latexConfig
        ).next_to ( mob_tex_standingWave, RIGHT, buff = 0.5 )

        # 计算频率
        
        mob_tex_freq = MathTex (
            r"f_1 = 1",
            **latexConfig
        ).next_to ( mob_tex_wavelength, RIGHT, buff = 0.5 )
        mob_tex_waveSpeed = MathTex (
            r"v = \lambda_1 f_1 = 2",
            **latexConfig
        ).next_to ( mob_tex_freq, RIGHT, buff = 0.5 )
        
        self.play (
            Succession (
                Write ( mob_tex_wavelength, run_time = 0.5 ),
                Wait ( 0.25 ),
                Write ( mob_tex_freq, run_time = 0.5 ),
                Wait ( 0.25 ),
                Write ( mob_tex_waveSpeed, run_time = 0.5 ),
                Wait ( 0.5 ),
            )
        )
        
        self.play (
            Transform (  
                mob_tex_freq,
                MathTex ( f"f_k = k", **latexConfig )\
                    .next_to ( mob_tex_wavelength, RIGHT, buff = 0.5 )
            ),
            FadeOut ( mob_tex_waveSpeed, run_time = 0.5 ),
        )
        
        mob_tex_standingWaveNew = MathTex ( 
            r"y_k(x, t) =",
            r"\sin (\pi k x)",
            r"\sin (2 \pi k t)",
            **latexConfig 
        ).next_to ( mob_text_title, RIGHT, buff = 0.75 )\
            .align_to ( mob_text_title, UP ) 
        mob_tex_wavelengthCp = mob_tex_wavelength.copy ( )\
            .next_to ( mob_tex_standingWaveNew, RIGHT, buff = 0.5 )
        mob_tex_freqCp = mob_tex_freq.copy ( )\
            .next_to ( mob_tex_wavelengthCp, RIGHT, buff = 0.5 )
        
        self.play (
            Transform ( mob_tex_standingWave, mob_tex_standingWaveNew ),
            Transform ( mob_tex_wavelength, mob_tex_wavelengthCp ),
            Transform ( mob_tex_freq, mob_tex_freqCp ),
        )
        
        # 介绍振动模式
        
        mob_text_note2 = Text (
            "这些振动模式称为单弦振动的简正模式 (normal modes)",
            **textConfig,
        ).next_to ( mob_tex_standingWave, DOWN, buff = 0.2 )\
            .align_to ( mob_text_note1, LEFT )
        mob_text_note3 = Tex (
            r"其振动频率都是 $f_1$ 的正整数倍.",
            **latexConfig,
        ).next_to ( mob_text_note2, DOWN, buff = 0.2 )\
            .align_to ( mob_text_note1, LEFT )
        mob_text_note4 = Tex (
            r"$f_1$称为基频 (fundamental frequency), 由单弦的物理性质决定",
            **latexConfig,
        ).next_to ( mob_text_note3, DOWN, buff = 0.2 )\
            .align_to ( mob_text_note1, LEFT )
        
        self.play (  
            Succession (
                Write ( mob_text_note2, run_time = 1 ),
                Write ( mob_text_note3, run_time = 1 ),
                Write ( mob_text_note4, run_time = 1 ),
            )
        )
        
        # 隐藏反向波形
        self.play ( 
            *( Uncreate ( mob [ 3 ] ) for mob in l_mob_waveDiagrams ),
            *( 
                Transform ( 
                    mob [ 4 ], 
                    mob [ 0 ].copy ( )\
                        .set_stroke ( opacity = 1, color = RED ) ) 
                for mob in l_mob_waveDiagrams 
            ),
            run_time = 0.5,
            rate_func = rate_functions.ease_in_quad,
        )
        
        T = 2
        animateTime = 15
        mob_var_t = ValueTracker ( 0 )
        
        def makeDiagramWaveformUpdater ( k, position ):
            wl = 2 / k * diagramStringLength
            def _updater ( mob ):
                t = mob_var_t.get_value ( )
                mob_curve_newWaveform = FunctionGraph (
                    lambda x: diagramAmp * np.sin ( TAU * x / wl ) * np.sin ( k * TAU * t / T ),
                    color = RED,
                    x_range = [ 0, diagramStringLength ],
                ).shift ( position )
                mob.become ( mob_curve_newWaveform )
            return _updater
        
        for k in range ( 1, 7 ):
            mob_wave = l_mob_waveDiagrams [ k - 1 ] [ 4 ]
            mob_wave.add_updater ( 
                makeDiagramWaveformUpdater ( 
                    k, l_mob_waveDiagrams [ k - 1 ] [ 1 ].get_center ( ) 
                ) 
            )
            
        self.play ( 
            mob_var_t.animate ( run_time = animateTime, rate_func = linear )\
                .increment_value ( animateTime ) 
        )

class SummedWaveScene ( Scene ):
    def construct ( self ):
        self.camera.background_color = "#282c34"
        
        _, exampleWaveform = analyzeSoundFile ( 
            DIR/r"assets/sound/piano.wav",
            **analyzeConfig,
        )
        cutoffWaveform = exampleWaveform [ :4 ]
        
        stringY = -1
        stringLength = 12
        amp = 1.5
        period = 2
        stringRight = np.array (( stringLength / 2, 0, 0 ))
        stringLeft = -stringRight
        
        mob_text_title = Text ( "单弦驻波的叠加", **(textConfig | {"font_size": 64}) )\
            .to_corner ( UL )
        mob_text_note1 = Text (
            "不同的简正模式可以依振幅和相位进行叠加，形成更为复杂的振动模式",
            **textConfig,
        ).next_to ( mob_text_title, DOWN, buff = 0.5 )\
            .align_to ( mob_text_title, LEFT )
        mob_tex_standingWave = MathTex (
            r"y_k(x, t) =",
            r"\sin \left(\pi k x",
            r"\right)",
            r"\sin (2 \pi kt)",
            **latexConfig
        ).next_to ( mob_text_note1, DOWN, buff = 0.5 )\
            .align_to ( mob_text_title, LEFT )
        mob_tex_summedWave = MathTex (
            r"y(x, t) = ",
            r"\sum_{k=1}^{+\infty}",
            r"A_k",
            r"\sin (\pi kx)",
            r"\sin (2\pi k t + \varphi_k)",
            **latexConfig
        ).next_to ( mob_tex_standingWave, RIGHT, buff = 0.5 )
        
        mob_var_t = ValueTracker ( 0 )
        mob_seg_string = Line (
            stringLeft, stringRight,
            color = WHITE,
        ).set_stroke ( opacity = 0.5 ).shift ( UP * stringY )
        mob_dot_stringLeft = Dot ( stringLeft, radius = 0.06 )\
            .shift ( UP * stringY )
        mob_dot_stringRight = Dot ( stringRight, radius = 0.06 )\
            .shift ( UP * stringY )
        
        def createStringCurve ( ):
            t = mob_var_t.get_value ( )
            return FunctionGraph (
                lambda x: amp * exampleWaveform.calcStandingWave ( x / stringLength, t / period ),
                x_range = [ 0, stringLength ],
                color = RED,
            ).shift ( stringLeft + UP * stringY )
        
        def createSineCurve ( k ):
            t = mob_var_t.get_value ( )
            return FunctionGraph (
                lambda x: ( 
                    cutoffWaveform.calcStandingWaveComponent ( 
                        k, x / stringLength, t / period 
                    ) * amp
                ),
                x_range = [ 0, stringLength ],
                color = RED,
            ).shift ( stringLeft + UP * stringY )\
                .set_stroke ( opacity = 0.5 )
        
        def createSineWaveUpdater ( k ):
            return lambda: createSineCurve ( k )
        
        l_mob_curve_sines = [ 
            always_redraw ( createSineWaveUpdater ( k ) ) 
            for k in range ( 1, len ( cutoffWaveform ) + 1 ) 
        ]
        mob_curve_string = always_redraw ( createStringCurve )
        mob_tex_standingWaveCp = mob_tex_standingWave.copy ( )
        
        self.play ( Write ( mob_text_title, run_time = 1 ) )
        self.play (
            Succession (
                Write ( mob_text_note1, run_time = 1 ),
                Write ( mob_tex_standingWave, run_time = 1 ),
            )
        )
        self.play (
            Transform ( mob_tex_standingWaveCp, mob_tex_summedWave ),
        )
        self.remove ( mob_tex_standingWaveCp )
        self.add ( mob_tex_summedWave )
        
        self.play (
            Create ( mob_seg_string, run_time = 1 ),
            Create ( mob_curve_string, run_time = 1 ),
            ( Create ( mob, run_time = 1 ) for mob in l_mob_curve_sines ),
            FadeIn ( mob_dot_stringLeft, run_time = 0.5 ),
            FadeIn ( mob_dot_stringRight, run_time = 0.5 ),
        )
        
        runTime = 15
        
        self.play (
            mob_var_t.animate ( run_time = runTime, rate_func = smoothStart ( 0.1 ) )\
                .set_value ( runTime ),
        )
        
class WaveformScene ( ThreeDScene ):
    def construct ( self ):
        self.camera.background_color = "#282c34"
        
        rx = config [ "frame_x_radius" ]
        ry = config [ "frame_y_radius" ]
        waveformY = -1.1
        wl = 4
        amp = 1.25
        period = 1.5
        periodRectHeight = ( ry + waveformY - 0.8 ) * 2
        runTime = 2 * rx / wl * period
        
        _, exampleWaveform = analyzeSoundFile ( 
            DIR/"assets/sound/violin.wav",
            **analyzeConfig,
        )
        
        mob_text_title = Text ( "波形图与傅里叶级数", **(textConfig | {"font_size": 64}) )\
            .to_corner ( UL )
        mob_text_note1 = Tex (
            r"删去单弦振动表达式中关于位置 $x$ 的正弦项，",
            **latexConfig,
        ).next_to ( mob_text_title, DOWN, buff = 0.5 )\
            .align_to ( mob_text_title, LEFT )
        mob_text_note2 = Tex (
            r"得到一个只依赖于时间 $t$ 的表达式 $h(t)$",
            **latexConfig,
        ).next_to ( mob_text_note1, DOWN, buff = 0.25 )\
            .align_to ( mob_text_title, LEFT )
        mob_text_note3 = Text (
            "该表达式可以近似反应单弦的总体振动状态",
            **textConfig,
        ).next_to ( mob_text_note2, DOWN, buff = 0.25 )\
            .align_to ( mob_text_title, LEFT )
        
        mob_vg_note12 = VGroup ( mob_text_note1, mob_text_note2 )
        
        mob_tex_summedWave = MathTex (
            r"y(x, t) = ",
            r"\sum_{k=1}^{+\infty}",
            r"A_k",
            r"\sin (\pi kx)",
            r"\sin (2\pi k t + \varphi_k)",
            **latexConfig
        ).next_to ( mob_vg_note12, RIGHT, buff = 0.75 )
        mob_tex_waveform = MathTex (
            r"h(t) = ",
            r"\sum_{k=1}^{+\infty}",
            r"A_k",
            r"\sin (2\pi k t + \varphi_k)",
            **latexConfig
        ).next_to ( mob_vg_note12, RIGHT, buff = 1 )
        
        self.play ( Write ( mob_text_title ) )
        self.play ( 
            Write ( mob_text_note1 ),
            FadeIn ( mob_tex_summedWave ),
            run_time = 1, 
        )
        self.play (  
            Succession (
                Transform ( mob_tex_summedWave, mob_tex_waveform ),
                Write ( mob_text_note2, run_time = 1 ),
                Write ( mob_text_note3, run_time = 1 ),
            )
        )
        self.wait ( 1 )
        self.play ( 
            FadeOut ( 
                mob_text_note1, mob_text_note2, mob_text_note3, 
                run_time = 0.5 
            ),
            Transform (
                mob_tex_summedWave,
                mob_tex_waveform\
                    .next_to ( mob_text_title, DOWN, buff = 0.3 )\
                    .align_to ( mob_text_title, LEFT ),
                run_time = 1,
            ),
        )
        self.remove ( mob_tex_summedWave )
        self.add ( mob_tex_waveform )
        
        mob_text_note4 = Text (
            "此表达式的图像称为波形图 (waveform diagram)",
            **textConfig,
        ).next_to ( mob_tex_waveform, RIGHT, buff = 0.5 )\
            .shift ( UP * 0.1 )
        mob_text_note5 = Text (
            "注：不同于前面的振动模式图，波形图以时间而不是位置作为横坐标",
            **( textConfig | {"font_size": 19} ),
        ).next_to ( mob_text_note4, DOWN, buff = 0.25 )\
            .align_to ( mob_text_note4, LEFT )
        mob_text_note6 = Text (
            "可以看出，波形图是由频率为基频正整数倍、振幅相位各异的正弦函数叠加而成",
            **textConfig,
        ).next_to ( mob_tex_waveform, DOWN, buff = 0.1 )\
            .align_to ( mob_text_title, LEFT )
        mob_line_timeline = Line (
            ( -rx, waveformY, 0 ),
            ( rx, waveformY, 0 ),
            color = WHITE,
        ).set_stroke ( opacity = 0.5 )
        mob_curve_exampleWaveform = FunctionGraph (
            lambda t: exampleWaveform ( t / wl ) * amp,
            x_range = [ 0, 2 * rx ],
            color = PURE_GREEN,
        ).shift (( -rx, waveformY, 0 ))
        
        mob_rect_onePeriod = Rectangle (
            width = wl,
            height = periodRectHeight,
        ).shift ( ( -rx + wl / 2, waveformY, 0 ) )\
            .set_fill ( color = WHITE, opacity = 0.25 )\
            .set_stroke ( width = 0 )
        
        self.play ( Write ( mob_text_note4, run_time = 1 ) )
        self.play ( 
            Create ( mob_line_timeline ),
            Create ( mob_curve_exampleWaveform ),
        )
        self.play ( FadeIn ( mob_text_note5, run_time = 1 ) )
        
        mob_var_t = ValueTracker ( 0 )
        mob_dot_pointOnWaveform = createGlow ( Dot ( radius = 0.06 ), color = PURE_GREEN )
        mob_seg_pointToTimeline = Line ( ( -2 * rx, 0, 0 ), ( -2 * rx, 1, 0 ) )
        
        def _calcPosition ( t ):
            x = t / period * wl - rx
            y = exampleWaveform ( t / period ) * amp + waveformY
            return x, y
        
        def updateLine ( mob ):
            t = mob_var_t.get_value ( )
            x, y = _calcPosition ( t )
            mob.put_start_and_end_on ( 
                ( x, waveformY, 0 ), 
                ( x, y, 0 ) 
            )
        def updateDot ( mob ):
            t = mob_var_t.get_value ( )
            x, y = _calcPosition ( t )
            mob.move_to ( ( x, y, 0 ) )
            
        mob_seg_pointToTimeline.add_updater ( updateLine )
        mob_dot_pointOnWaveform.add_updater ( updateDot )
        
        self.add ( mob_seg_pointToTimeline )
        self.play (
            mob_var_t.animate.set_value ( runTime ),
            MoveAlongPath ( mob_dot_pointOnWaveform, mob_curve_exampleWaveform ),
            run_time = runTime, rate_func = linear,
        )
        self.remove ( mob_seg_pointToTimeline, mob_dot_pointOnWaveform )
        
        self.play ( 
            Create ( mob_rect_onePeriod ),
            run_time = 1,
        )
        
        # 将波形放大到一个周期
        
        stretchFactor = 2 * rx / wl
        self.play (
            Succession (
                AnimationGroup (
                    mob_rect_onePeriod.animate\
                        .stretch_to_fit_width ( 2 * rx )\
                        .move_to ( ( 0, waveformY, 0 ) )\
                        .set_fill ( opacity = 0.1 ),
                    mob_curve_exampleWaveform.animate\
                        .stretch ( stretchFactor, 0 )\
                        .move_to ( ( ( stretchFactor - 1 ) * rx, waveformY, 0 ) ),
                    run_time = 1.5,
                ),
                FadeOut ( mob_rect_onePeriod, run_time = 0.25 )
            ),
            FadeOut ( mob_text_note5, run_time = 0.5 ),
            Write ( mob_text_note6, run_time = 1 ),
        )
        
        # 展示正弦波的叠加
        
        n = len ( exampleWaveform )
        cutoffWaves = [ exampleWaveform [ :k ] for k in range ( 1, n ) ]
        cutoffWaves.append ( exampleWaveform )
        
        l_mob_curve_sines = [ ]
        l_mob_curve_cutoffWaves = [ ]
        norms = np.empty ( n, dtype = float )
        for k in range ( 1, n + 1 ):
            norms [ k - 1 ] = np.linalg.norm ( exampleWaveform.data [ :k ] )
        
        def createWaveformGraph ( fn ):
            return FunctionGraph ( 
                    lambda t: fn ( t / rx / 2 ) * amp, 
                    x_range = [ 0, 2 * rx ], color = PURE_GREEN 
            ).shift ( ( -rx, waveformY, 0 ) )
        
        for i, coef in enumerate ( exampleWaveform ):
            k = i + 1
            fn = lambda t: ( np.exp ( 1j * TAU * k * t ) * coef ).imag
            l_mob_curve_sines.append (
                createWaveformGraph ( fn ).set_stroke ( opacity = 0.5 )
            )
        
        self.wait ( 2 )
        self.play ( 
            mob_curve_exampleWaveform.animate.stretch_to_fit_height ( 0 ),
            run_time = 0.5
        )
        
        mob_curve_exampleWaveform.become (
            mob_line_timeline.copy ( ).set_color ( PURE_GREEN )
        )
        
        for i, mob in enumerate ( l_mob_curve_sines ):
            mob.stretch_to_fit_height ( 
                np.abs ( exampleWaveform [ i + 1 ] ) / 
                norms [ i ] * amp * 2
            )
            self.play ( 
                Create ( mob ),
                ( 
                    l_mob_curve_sines [ j ].animate\
                        .stretch_to_fit_height ( 
                            np.abs ( exampleWaveform [ j + 1 ] ) / 
                            norms [ i ] * amp * 2
                        )\
                        .set_stroke ( opacity = 0.2 ) 
                    for j in range ( i ) 
                ),
                run_time = 0.75
            )
            mob_curve_newWaveform = createWaveformGraph ( cutoffWaves [ i ] )
            mob_curve_sineCp = mob.copy ( )
            self.add ( mob_curve_sineCp )
            self.play ( 
                Transform ( mob_curve_exampleWaveform, mob_curve_newWaveform ),
                Transform ( mob_curve_sineCp, mob_curve_newWaveform ) 
            )
            mob_curve_newWaveform.set_stroke ( opacity = 0.5 )
            l_mob_curve_cutoffWaves.append ( mob_curve_newWaveform )
            self.remove ( mob_curve_sineCp )
            self.wait ( 0.25 )
        
        self.wait ( 2 )
        
        self.remove (
            mob_text_title,
            mob_tex_waveform,
            mob_text_note4,
            mob_text_note6,
        )
        self.add_fixed_in_frame_mobjects (
            mob_text_title,
            mob_tex_waveform,
            mob_text_note4,
            mob_text_note6,
        )
        
        # 三维分离效果
        
        mob_var_theta, mob_var_phi, mob_var_gamma, mob_var_zoom = (
            self.camera.theta_tracker,
            self.camera.phi_tracker,
            self.camera.gamma_tracker,
            self.camera.zoom_tracker,
        )
        print ( mob_curve_exampleWaveform.get_stroke_width ( ) )
        self.play (
            mob_var_phi.animate.set_value ( -PI / 6 ),
            mob_var_theta.animate.increment_value ( -PI / 3 ),
            mob_var_gamma.animate.increment_value ( -64 * DEGREES ),
            mob_var_zoom.animate.set_value ( 0.6 ),
            FadeOut ( mob_line_timeline ),
            mob_curve_exampleWaveform.animate\
                .shift ( OUT * ( n // 2 ) )\
                .set_fill ( opacity = 0.1 )\
                .set_stroke ( width = 6 ),
            (
                mob.animate.shift ( IN * ( i + 1 - n // 2 ) ).set_stroke ( opacity = 0.5 )
                for i, mob in enumerate ( l_mob_curve_sines )
            ),
        )
        
        # 正弦波分量闪动效果
        
        last_mob = None
        for i, mob in enumerate ( l_mob_curve_sines ):
            time = rate_functions.ease_in_out_cubic ( i / ( n - 1 ) ) * 0.25 + 0.1
            if last_mob is not None:
                self.play (
                    last_mob.animate.set_stroke ( opacity = 0.5 ),
                    mob.animate.set_stroke ( opacity = 1 ),
                    run_time = time,
                )
            else:
                self.play (
                    mob.animate.set_stroke ( opacity = 1 ),
                    run_time = time,
                )
            last_mob = mob
        self.play (
            last_mob.animate.set_stroke ( opacity = 0.5 ),
            run_time = 0.25,
        )
        self.wait ( 2 ) 
        
        # 回归平面
        
        self.play (
            mob_var_phi.animate.set_value ( 0 ),
            mob_var_theta.animate.set_value ( -PI / 2 ),
            mob_var_gamma.animate.set_value ( 0 ),
            mob_var_zoom.animate.set_value ( 1 ),
            mob_curve_exampleWaveform.animate\
                .set_coord ( 0, 2 )\
                .set_fill ( opacity = 0 )\
                .set_stroke ( width = 4 ),
            ( 
                mob.animate.set_coord ( 0, 2 )\
                    .set_stroke ( opacity = 0.25 ) 
                for mob in l_mob_curve_sines 
            ),
            FadeIn ( mob_line_timeline, run_time = 1 ),
        )
        
        # 不同数量正弦波的逼近结果叠加
        
        self.play (
            *( FadeOut ( mob, run_time = 0.25 ) for mob in l_mob_curve_sines ),
        )
        self.play ( 
            Succession (
                *( 
                    FadeIn ( mob, run_time = 0.25 ) 
                    for mob in l_mob_curve_cutoffWaves [ :-1 ] 
                )
            )
        )
        self.wait ( 2 )
        
        # 隐藏波形图
        
        self.play (
            LaggedStart (
                *( 
                    Transform ( mob, mob_line_timeline, run_time = 0.5 ) 
                    for mob in l_mob_curve_cutoffWaves 
                ),
                Transform ( mob_curve_exampleWaveform, mob_line_timeline, run_time = 0.5 ),
                lag_ratio = 0.1,
            ),
        )
        self.remove ( *l_mob_curve_cutoffWaves, mob_curve_exampleWaveform )
        self.play ( Uncreate ( mob_line_timeline ), run_time = 0.75 )
        
        # 进一步解释傅里叶级数
        
        mob_text_note7 = Text ( "像这样的表达式称作一个傅里叶级数", **textConfig )\
            .next_to ( mob_text_note6, DOWN, buff = 0.3 )\
            .align_to ( mob_text_title, LEFT )
        mob_text_note8 = Text ( 
            "(虽然这并非傅里叶级数最常见的形式)", 
            **( textConfig | {"font_size": 19} ) 
        )\
            .next_to ( mob_text_note7, RIGHT, buff = 0.5 )\
            .align_to ( mob_text_note7, DOWN )
        mob_text_fourierRealNote = Text ( "实数形式", **textConfig )\
            .next_to ( mob_text_note8, DOWN, buff = 0.6 )\
            .align_to ( mob_text_title, LEFT )
        mob_tex_fourierReal = MathTex (
            r"h(t) = \frac{a_0}{2} + \sum_{k=1}^{+\infty}",
            r"a_k \cos (2\pi k t)", r"+",
            r"b_k \sin (2\pi k t)",
            **latexConfig
        ).next_to ( mob_text_fourierRealNote, RIGHT, buff = 0.5 )
        # mob_tex_fourierCoefReal_a0 = MathTex (
        #     r"a_0 = \int_{0}^{1} h(t) \text{d}t",
        #     **latexConfig
        # ).next_to ( mob_tex_fourierReal, RIGHT, buff = 0.75 )
        # mob_tex_fourierCoefReal_ak = MathTex (
        #     r"a_k = \int_{0}^{1} h(t) \cos (2\pi k t) \text{d}t",
        #     **latexConfig
        # ).next_to ( mob_tex_fourierCoefReal_a0, RIGHT, buff = 0.5 )
        # mob_text_fourierCoefReal_bk = MathTex (
        #     r"b_k = \int_{0}^{1} h(t) \sin (2\pi k t) \text{d}t",
        #     **latexConfig
        # ).next_to ( mob_tex_fourierCoefReal_ak, RIGHT, buff = 0.5 )
        
        mob_text_fourierComplexNote = Text ( "复数形式", **textConfig )\
            .next_to ( mob_text_fourierRealNote, DOWN, buff = 0.6 )\
            .align_to ( mob_text_title, LEFT )
        mob_tex_fourierComplex = MathTex (
            r"h(t) = \sum_{k \in \mathbb{Z}}",
            r"\hat{h}(k) \text{e}^{2\pi \text{i} k t}",
            **latexConfig
        ).next_to ( mob_text_fourierComplexNote, RIGHT, buff = 0.5 )
        # mob_tex_fourierCoefComplex = MathTex (
        #     r"\hat{h}(k) =",
        #     r"\int_{0}^{1} h(t) \text{e}^{-2\pi \text{i} k t} \text{d}t",
        #     **latexConfig
        # ).next_to ( mob_tex_fourierComplex, RIGHT, buff = 0.75 )
        
        mob_text_note9 = Text ( 
            "通过配凑余弦项可以将其转化为工程学中更常用的复数形式",
            **textConfig
        ).next_to ( mob_text_note8, DOWN, buff = 0.25 )\
            .align_to ( mob_text_title, LEFT )
        mob_tex_waveformComplex = MathTex (
            r"h_{\text{c}}(t) = \sum_{k = 1}^{+\infty} A_k ",
            r"\cos (2\pi kt + \varphi_k) + \text{i} \sin (2\pi kt + \varphi_k)",
            **latexConfig
        ).next_to ( mob_text_note9, DOWN, buff = 0.25 )\
            .align_to ( mob_text_title, LEFT )
        
        self.play (
            Succession (
                Write ( mob_text_note7, run_time = 1 ),
                Write ( mob_text_note8, run_time = 1 ),
                AnimationGroup (
                    FadeIn ( 
                        mob_text_fourierRealNote, 
                        mob_tex_fourierReal,
                        mob_text_fourierComplexNote,
                        mob_tex_fourierComplex,
                        run_time = 1 
                    ),

                ),
            ),
        )
        self.wait ( 1 )
        self.play (
            Succession (
                FadeOut (
                    mob_text_fourierRealNote, 
                    mob_text_fourierComplexNote, 
                    mob_tex_fourierReal, 
                    mob_tex_fourierComplex,
                    run_time = 0.5,
                ),
                Write ( mob_text_note9, run_time = 1 ),
            )
        )
        mob_tex_waveformCp = mob_tex_waveform.copy ( )
        self.play (
            Transform ( mob_tex_waveformCp, mob_tex_waveformComplex, run_time = 1 )
        )
        self.remove ( mob_tex_waveformCp )
        self.add ( mob_tex_waveformComplex )
        self.play (
            Transform (
                mob_tex_waveformComplex,
                MathTex (
                    r"h_{\text{c}}(t) = ",
                    r"\sum_{k=1}^{+\infty}",
                    r"(A_k \text{e}^{\text{i} \varphi_k}) \text{e}^{2\pi \text{i} k t}",
                    **latexConfig
                ).next_to ( mob_text_note9, DOWN, buff = 0.25 )\
                    .align_to ( mob_text_title, LEFT ),
                run_time = 1,
            )
        )
        
        mob_tex_complexFormToRealForm = MathTex (
            r"h(t) = \text{Im} \left( h_{\text{c}}(t) \right)",
            **latexConfig
        ).next_to ( mob_tex_waveformComplex, RIGHT, 0.5 )\
            .shift ( UP * 0.05 )
        
        self.play (  Write ( mob_tex_complexFormToRealForm ), run_time = 0.5 )
        
        self.wait ( 5 )

class FrequencyAndTimeDomainScene ( Scene ):
    def construct ( self ):
        self.camera.background_color = "#282c34"
        
        rx = config [ "frame_x_radius" ]
        ry = config [ "frame_y_radius" ]
        space = 0.5
        w = ( 2 * rx - 3 * space ) / 2
        h = 3.5
        graphY = 0
        phaseAreaRatio = 0.4
        dividerY = graphY + h * ( phaseAreaRatio - 0.5 )
        timelineLeft = np.array (( -rx + space, graphY, 0 ))
        timelineRight = timelineLeft + RIGHT * w
        dividerLeft = np.array (( space / 2, dividerY, 0 ))
        dividerRight = dividerLeft + RIGHT * w
        waveBuff = 0.5
        waveAmp = h / 2 - waveBuff
        nHarmonics = 10
        barSpace = 0.2
        barBuff = 0.25
        barWidth = ( w - ( nHarmonics + 1 ) * barSpace ) / nHarmonics
        ampBarMaxHeight = h * ( 1 - phaseAreaRatio ) - barBuff
        phaseBarMaxHeight = h * phaseAreaRatio - barBuff
        
        mob_text_title = Text ( "时域与频域", **( textConfig | { "font_size": 84 } ) )\
            .to_edge ( UL, buff = 0.5 )
        mob_rect_waveformArea = Rectangle ( width = w, height = h )\
            .to_edge ( LEFT, buff = space )\
            .set_coord ( graphY, 1 )
        mob_seg_timeline = Line ( timelineLeft, timelineRight )\
            .set_stroke ( opacity = 0.5 )
        mob_seg_divider = Line ( dividerLeft, dividerRight )\
            .set_stroke ( opacity = 0.5 )
        mob_rect_spectrumArea = mob_rect_waveformArea.copy ( )\
            .next_to ( mob_rect_waveformArea, RIGHT, buff = space )\
            .set_coord ( graphY, 1 )
            
        _, waveform = analyzeSoundFile ( 
            DIR/"assets/sound/violin.wav",
            **analyzeConfig,
        )
        waveformMax = findMax ( waveform )
        
        mob_curve_waveform = FunctionGraph (
            lambda t: waveform ( t / w ) / waveformMax * waveAmp,
            x_range = ( 0, w ),
            color = PURE_GREEN,
        ).shift ( timelineLeft )
        
        coefs = np.array ( [ waveform [ k ] for k in range ( 1, nHarmonics + 1 ) ] )
        amplitudes = np.abs ( coefs )
        phases = np.angle ( coefs )
        maxAmp = np.max ( amplitudes )
        phases [ 0 ] = 0
        phases [ phases < 0 ] += TAU
        
        mob_vg_amblitudeBars = VGroup ( )
        mob_vg_phaseBars = VGroup ( )
        
        for i, ( a, ph ) in enumerate ( zip ( amplitudes, phases ) ):
            ampBarHeight = a / maxAmp * ampBarMaxHeight
            phaseBarHeight = ph / TAU * phaseBarMaxHeight
            barX = ( i + 1 ) * barSpace + i * barWidth + space / 2
            mob_vg_amblitudeBars.add (
                Polygon (
                    ( barX, dividerY, 0 ),
                    ( barX + barWidth, dividerY, 0 ),
                    ( barX + barWidth, dividerY + ampBarHeight, 0 ),
                    ( barX, dividerY + ampBarHeight, 0 ),
                    fill_opacity = 0.5,
                    fill_color = BLUE,
                    color = BLUE,
                )
            )
            mob_vg_phaseBars.add (
                Polygon (
                    ( barX, dividerY, 0 ),
                    ( barX + barWidth, dividerY, 0 ),
                    ( barX + barWidth, dividerY - phaseBarHeight, 0 ),
                    ( barX, dividerY - phaseBarHeight, 0 ),
                    fill_opacity = 0.5,
                    fill_color = PURPLE,
                    color = PURPLE,
                )
            )
        
        self.play (  Write ( mob_text_title ), run_time = 1 )
        self.play (
            FadeIn ( mob_rect_waveformArea, mob_rect_spectrumArea ),
            Create ( mob_seg_timeline ),
            Create ( mob_seg_divider ),
            run_time = 0.5,
        )
        self.play (
            Create ( mob_curve_waveform ),
            Create ( mob_vg_amblitudeBars ),
            Create ( mob_vg_phaseBars ),
            run_time = 0.5,
        )
        
        mob_text_amplitude = Text ( "振幅", **textConfig )\
            .align_to ( mob_rect_spectrumArea, UR )\
            .shift ( ( -0.2, -0.2, 0 ) )
        mob_text_phase = Text ( "相位", **textConfig )\
            .align_to ( mob_rect_spectrumArea, DR )\
            .shift ( ( -0.2, 0.2, 0 ) )
        mob_text_phaseStartValue = Text ( "0", **( textConfig | { "font_size": 20 } ) )\
            .align_to ( mob_seg_divider, UL )\
            .shift ( ( 0.1, -0.1, 0 ) )
        mob_text_phaseEndValue = Text ( "2π", **( textConfig | { "font_size": 20 } ) )\
            .align_to ( mob_rect_spectrumArea, DL )\
            .shift ( ( 0.1, 0.1, 0 ) )
        
        self.play (
            Write ( mob_text_amplitude ),
            Write ( mob_text_phase ),
            FadeIn ( mob_text_phaseStartValue, mob_text_phaseEndValue ),
            run_time = 0.5,
        )
        
        mob_text_timeDomain = Text ( "波形图——时域", **( textConfig | {"font_size": 36} ) )\
            .next_to ( mob_rect_waveformArea, DOWN, buff = 0.3 )
        mob_text_freqDomain = Text ( "频谱图——频域", **( textConfig | {"font_size": 36} ) )\
            .next_to ( mob_rect_spectrumArea, DOWN, buff = 0.3 )
        
        self.play (
            Write ( mob_text_timeDomain ),
            Write ( mob_text_freqDomain ),
            run_time = 1,
        )
        
        mob_seg_playhead = Line ( ORIGIN, h * UP )\
            .move_to ( timelineLeft )
        mob_var_t = ValueTracker ( 0 )
        
        def updatePlayhead ( mob ):
            t = mob_var_t.get_value ( ) % 1
            playheadX = ( t - 1 ) * w - space / 2
            mob.set_coord ( playheadX, 0 )
        
        def updatePoint ( mob ):
            t = mob_var_t.get_value ( ) % 1
            x = ( t - 1 ) * w - space / 2
            y = waveform ( t ) * waveAmp / waveformMax + graphY
            mob.move_to ( ( x, y, 0 ) )
        
        mob_dot_pointOnWaveform = createGlow ( Dot ( ), color = PURE_GREEN )
        
        mob_seg_playhead.add_updater ( updatePlayhead )
        mob_dot_pointOnWaveform.add_updater ( updatePoint )
        
        period = 2
        nPeriods = 20
        
        self.add ( mob_seg_playhead, mob_dot_pointOnWaveform )
        self.play (
            mob_var_t.animate ( 
                run_time = period * nPeriods,
                rate_func = smoothStart ( 0.1 ), 
            ).set_value ( nPeriods ),
        )

class WaveDemoScene ( Scene ):
    def construct ( self ):
        self.camera.background_color = "#282c34"
        rx = config [ "frame_x_radius" ]
        ry = config [ "frame_y_radius" ]
        space = 0.5
        w1 = 5
        h = 3
        w2 = h
        w3 = 2 * rx - w1 - w2 - 4 * space
        phaseAreaRatio = 0.3
        stringY = 1.75
        stringLen = 12
        stringRight = np.array (( stringLen / 2, stringY, 0 ))
        stringLeft = np.array (( -stringLen / 2, stringY, 0 ))
        nHarmonics = 10
        waveformBuff = 0.2
        amp = h / 2 - waveformBuff
        vibAmp = 1.5
        nPeriods = 15.25
        period = 1
        runTime = nPeriods * period
        basicWaveformExpansion = 80
        
        mob_rect_waveformArea = Rectangle (
            width = w1,
            height = h,
        ).to_corner ( DL, buff = space )
        mob_rect_complexWaveformArea = Rectangle (
            width = w2, height = h,
        ).next_to ( mob_rect_waveformArea, RIGHT, buff = space )
        mob_rect_spectrumArea = Rectangle (
            width = w3, height = h,
        ).next_to ( mob_rect_complexWaveformArea, RIGHT, buff = space )
        mob_seg_ampPhaseDivider = Line ( ORIGIN, RIGHT * w3 )\
            .to_corner ( DR, buff = space )\
            .shift ( UP * h * phaseAreaRatio )
        
        mob_seg_string = Line ( stringLeft, stringRight ).set_stroke ( opacity = 0.5 )
        mob_dot_stringLeft = Dot ( stringLeft, radius = 0.06 )
        mob_dot_stringRight = Dot ( stringRight, radius = 0.06 )
        
        mob_text_waveform = Text ( "波形图", **( textConfig | {"font_size": 40} ) )\
            .move_to ( mob_rect_waveformArea )
        mob_text_complexWaveform = Text ( "复数\n波形图", **( textConfig | {"font_size": 40} ) )\
            .move_to ( mob_rect_complexWaveformArea )
        mob_text_spectrum = Text ( "频谱图", **( textConfig | {"font_size": 40} ) )
        mob_text_spectrumNote = Text ( "(上方振幅、下方相位)", **textConfig )\
            .next_to ( mob_text_spectrum, DOWN, buff = 0.25 )
        VGroup ( mob_text_spectrum, mob_text_spectrumNote )\
            .move_to ( mob_rect_spectrumArea )
        mob_text_vibration = Text ( "振动模式图", **( textConfig | {"font_size": 40} ) )\
            .next_to ( mob_seg_string, UP, buff = 0.4 )
        
        spectrumOrigin = mob_seg_ampPhaseDivider.get_center ( ) + LEFT * w3 / 2
        
        self.play (
            LaggedStart (
                LaggedStart (
                    FadeIn ( mob_rect_waveformArea, run_time = 0.5 ),
                    FadeIn ( mob_rect_complexWaveformArea, run_time = 0.5 ),
                    FadeIn ( mob_rect_spectrumArea, run_time = 0.5 ),
                    Create ( mob_seg_string, run_time = 0.5 ),
                    FadeIn ( mob_dot_stringLeft, mob_dot_stringRight, run_time = 0.5 ),
                    lag_ratio = 0.25,
                ),
                LaggedStart (
                    Write ( mob_text_waveform, run_time = 0.5 ),
                    Write ( mob_text_complexWaveform, run_time = 0.5 ),
                    Write ( mob_text_spectrum, run_time = 0.5 ),
                    Write ( mob_text_spectrumNote, run_time = 0.5 ),
                    Write ( mob_text_vibration, run_time = 0.5 ),
                    lag_ratio = 0.25,
                ),
                lag_ratio = 0.5,
            )
        )
        self.wait ( 1 )
        
        waveY = mob_rect_waveformArea.get_coord ( 1 )
        complexWaveLeftX = -rx + space * 2 + w1
        waveLeftX = -rx + space
        waveLeft = np.array (( waveLeftX, waveY, 0 ))
        waveRight = waveLeft + RIGHT * w1
        complexWaveLeft = np.array (( complexWaveLeftX, waveY, 0 ))
        complexWaveCenter = complexWaveLeft + RIGHT * ( w2 / 2 )
        complexWaveRight = complexWaveLeft + RIGHT * w2
        complexWaveTop = complexWaveCenter + UP * ( h / 2 )
        complexWaveBottom = complexWaveCenter + DOWN * ( h / 2 )
        
        mob_var_t = ValueTracker ( 0 )
        
        mob_seg_timeline = Line ( waveLeft, waveRight )\
            .set_stroke ( opacity = 0.5 )
        mob_seg_complexWaveXAxis = Line ( complexWaveLeft, complexWaveRight )\
            .set_stroke ( opacity = 0.5 )
        mob_seg_complexWaveYAxis = Line ( complexWaveTop, complexWaveBottom )\
            .set_stroke ( opacity = 0.5 )
        mob_dot_complexWaveOrigin = Dot ( complexWaveCenter, radius = 0.06 )
        
        self.play (
            FadeOut (
                mob_text_waveform, 
                mob_text_complexWaveform, 
                mob_text_spectrum, 
                mob_text_spectrumNote, 
                mob_text_vibration,
            ),
            Create ( mob_seg_timeline ),
            Create ( mob_seg_complexWaveXAxis ),
            Create ( mob_seg_complexWaveYAxis ),
            Create ( mob_seg_ampPhaseDivider ),
            FadeIn ( mob_dot_complexWaveOrigin ),
            run_time = 0.5,
        )
        
        # 与波形有关的内容
        # 载入波形
        
        waveforms = (
            *(
                analyzeSoundFile ( 
                    DIR/f"assets/sound/{instrument}.wav",
                    **analyzeConfig
                ) [ 1 ]
                for instrument in (
                    "piano", 
                    "violin",
                    "oboe",
                    "trombone",
                )
            ),
            SineWave ( ),
            SquareWave ( ) [ :basicWaveformExpansion ],
            TriangleWave ( ) [ :basicWaveformExpansion ],
            SawtoothWave ( ) [ :basicWaveformExpansion ],
        )
        waveformNames = (
            "钢琴",
            "小提琴",
            "双簧管",
            "长号",
            "正弦波",
            "方波",
            "三角波",
            "锯齿波",
        )
        soundFileNames = (
            "piano",
            "violin",
            "oboe",
            "trombone",
            "sine",
            "square",
            "triangle",
            "sawtooth",
        )
        
        for waveform, waveformName, soundFileName in zip ( waveforms, waveformNames, soundFileNames ):
            mob_var_t.set_value ( 0 )
            waveMax = min ( findMax ( waveform ), 5 )
            
            mob_text_name = Text ( 
                    waveformName, 
                    **( textConfig | { "font_size": 32 } ) 
            ).to_corner ( UL )
            mob_curve_waveform = FunctionGraph (
                lambda t: waveform ( t / w1 ) * amp / waveMax,
                x_range = ( 0, w1 ),
                color = PURE_GREEN,
            ).shift ( waveLeft )
            mob_curve_complexWaveform = createBoundedParametricGraph (
                lambda t: complexToPoint ( waveform.calc ( t ) ) * amp / waveMax,
                x_range = ( -w2 / 2, w2 / 2 )
            ).shift ( mob_rect_complexWaveformArea.get_center ( ) )
            mob_dot_pointOnWaveform = Dot ( radius = 0.06 )
            mob_dot_pointOnComplexWaveform = Dot ( radius = 0.06 )
            mob_seg_timelineToWaveform = Line ( 
                ( waveLeftX, waveY - h / 2, 0 ),
                ( waveLeftX, waveY + h / 2, 0 ),
            )
            mob_seg_waveformToComplexWaveForm = Line ( )
            
            def createString ( ):
                t = mob_var_t.get_value ( )
                return FunctionGraph (
                    lambda x: waveform.calcStandingWave ( x / stringLen, t ) * vibAmp,
                    color = RED,
                    x_range = ( 0, stringLen ),
                ).shift ( stringLeft )
            
            def getCoordOnWaveform ( t ):
                x = waveLeftX + t * w1
                y = waveform ( t ) * amp / waveMax + waveY
                return  ( x, y, 0 )
            
            def getCoordOnComplexWaveform ( t ):
                z = waveform.calc ( t ) * amp / waveMax
                x, y = z.real, z.imag
                if x < -w2 / 2: x = -w2 / 2
                elif x > w2 / 2: x = w2 / 2
                return complexWaveCenter + ( x, y, 0 )
            
            def updatePointOnWaveform ( mob ):
                t = mob_var_t.get_value ( ) % 1
                mob.move_to ( getCoordOnWaveform ( t ) )
            
            def updatePointOnComplexWaveform ( mob ):
                t = mob_var_t.get_value ( ) % 1
                z = waveform.calc ( t ) * amp / waveMax
                x = z.real
                if x < -w2 / 2 or x > w2 / 2: mob.set_opacity ( 0 )
                else: mob.set_opacity ( 1 )
                mob.move_to ( getCoordOnComplexWaveform ( t ) )
            
            def updateLineToWaveform ( mob ):
                t = mob_var_t.get_value ( ) % 1
                mob.set_coord ( waveLeftX + t * w1, 0 )
            
            def updateLineToComplexWaveform ( mob ):
                t = mob_var_t.get_value ( ) % 1
                coordOnWaveform = getCoordOnWaveform ( t )
                coordOnComplexWaveform = getCoordOnComplexWaveform ( t )
                mob.put_start_and_end_on (
                    coordOnWaveform,
                    coordOnComplexWaveform,
                )
            
            mob_curve_string = always_redraw ( createString )
            
            mob_vg_spectrumAmp = VGroup ( )
            mob_vg_spectrumPhase = VGroup ( )
            
            coefs = np.array ( [ waveform [ k ] for k in range ( 1, nHarmonics + 1 ) ] )
            amps = np.abs ( coefs )
            phases = np.angle ( coefs )
            phases [ 0 ] = 0
            maxAmp = np.max ( amps )
            
            barGap = 0.1
            barWidth = ( w3 - barGap * ( nHarmonics + 1 ) ) / nHarmonics
            ampBarMaxHeight = ( 1 - phaseAreaRatio ) * h - waveformBuff
            phaseBarMaxHeight = phaseAreaRatio * h
            
            for i, ( a, ph ) in enumerate ( zip ( amps, phases ) ):
                ph %= TAU
                barX = ( i + 1 ) * barGap + i * barWidth
                ampBarHeight = a / maxAmp * ampBarMaxHeight
                phaseBarHeight = ph / TAU * phaseBarMaxHeight
                mob_ampBar = Polygon (
                    ( barX, 0, 0 ),
                    ( barX + barWidth, 0, 0 ),
                    ( barX + barWidth, ampBarHeight, 0 ),
                    ( barX, ampBarHeight, 0 ),
                    color = BLUE,
                ).set_fill ( BLUE, 0.5 )
                mob_phaseBar = Polygon (
                    ( barX, 0, 0 ),
                    ( barX + barWidth, 0, 0 ),
                    ( barX + barWidth, -phaseBarHeight, 0 ),
                    ( barX, -phaseBarHeight, 0 ),
                    color = PURPLE,
                ).set_fill ( PURPLE, 0.5 )
                mob_vg_spectrumAmp.add ( mob_ampBar )
                mob_vg_spectrumPhase.add ( mob_phaseBar )
            
            VGroup ( mob_vg_spectrumAmp, mob_vg_spectrumPhase )\
                .shift ( spectrumOrigin )
            
            self.play ( 
                Write ( mob_text_name ),
                Create ( mob_curve_waveform ),
                Create ( mob_curve_complexWaveform ),
                Create ( mob_curve_string ),
                Create ( mob_vg_spectrumAmp ),
                Create ( mob_vg_spectrumPhase ),
                run_time = 0.5,
            )
            
            mob_dot_pointOnWaveform.add_updater ( updatePointOnWaveform )
            mob_dot_pointOnComplexWaveform.add_updater ( updatePointOnComplexWaveform )
            mob_seg_timelineToWaveform.add_updater ( updateLineToWaveform )
            mob_seg_waveformToComplexWaveForm.add_updater ( updateLineToComplexWaveform )
            self.add (
                mob_dot_pointOnWaveform,
                mob_dot_pointOnComplexWaveform,
                mob_seg_timelineToWaveform,
                mob_seg_waveformToComplexWaveForm,
            )
            
            # self.add_sound ( DIR/f"assets/sound/{soundFileName}.wav" )
            self.play (
                mob_var_t.animate ( run_time = runTime, rate_func = smoothBoth ( 0.1 ) )\
                    .set_value ( nPeriods ),
            )
            for mob in (
                mob_dot_pointOnWaveform,
                mob_dot_pointOnComplexWaveform,
                mob_seg_timelineToWaveform,
                mob_seg_waveformToComplexWaveForm,
            ): mob.clear_updaters ( )
            
            mob_vg_spectrumAmp.invert ( )
            mob_vg_spectrumPhase.invert ( )
            self.wait ( 0.5 )
            self.play (
                Uncreate ( mob_curve_waveform ),
                Uncreate ( mob_curve_complexWaveform ),
                Uncreate ( mob_curve_string ),
                Uncreate ( mob_vg_spectrumAmp ),
                Uncreate ( mob_vg_spectrumPhase ),
                Uncreate ( mob_seg_waveformToComplexWaveForm ),
                Uncreate ( mob_seg_timelineToWaveform ),
                FadeOut ( 
                    mob_dot_pointOnWaveform, 
                    mob_dot_pointOnComplexWaveform,
                    mob_text_name, 
                ),
                run_time = 1,
            )

class PianoStructureScene ( Scene ):
    def construct ( self ):
        # 参考：https://wiwi.video/w/rioC1P2MN7RtgbfU6csBWC
        self.camera.background_color = "#282c34"
        mob_text_title = Text ( "钢琴的打击系统", **(textConfig | {"font_size": 64}) )\
            .to_corner ( UL )
        
        pivot = np.array (( 2, -1.75, 0 ))
        stringY = 0.75
        stringLength = 12
        pivotTriangleSize = ( 0.4, 0.2 )
        keyExtent = ( 5, 4 )
        damperSize = ( 1, 0.4 )
        hammerRadius = 0.3
        hammerPosition = 2.5
        
        pressTime = 0.5
        waitTime = 1
        hammerUpRatio = 0.25
        soundDelayRatio = 0.25
        wiggleFreq = 20
        wiggleDelay = pressTime * hammerUpRatio
        wiggleTime = pressTime * ( 2 - hammerUpRatio )
        maxAngle = PI / 36
        pressEasing = rate_functions.ease_in_out_cubic
        hammerUpEasing = rate_functions.ease_out_quad
        hammerDownEasing = rate_functions.ease_in_bounce
        
        mob_var_t = ValueTracker ( 0 )
        mob_var_tHammer = ValueTracker ( 0 )
        
        mob_dot_pivot = Dot ( pivot, radius = 0.06 )
        mob_triangle_pivot = Polygon (
            ORIGIN,
            DOWN * pivotTriangleSize [ 0 ] + LEFT * pivotTriangleSize [ 1 ],
            DOWN * pivotTriangleSize [ 0 ] + RIGHT * pivotTriangleSize [ 1 ],
            color = WHITE,
        ).shift ( pivot )
        mob_key = Line ( 
            LEFT * keyExtent [ 0 ], 
            RIGHT * keyExtent [ 1 ] 
        ).shift ( pivot )
        mob_string = Line (
            LEFT * ( stringLength / 2 ),
            RIGHT * ( stringLength / 2 ),
            color = RED,
        ).shift ( UP * stringY )
        mob_damperLinker = Line (
            UP * pivot [ 1 ], UP * stringY,
        ).shift ( RIGHT * ( pivot [ 0 ] - keyExtent [ 0 ] ) )
        mob_hammer = Circle ( hammerRadius, color = BLUE )\
            .move_to ( pivot + LEFT * hammerPosition + UP * hammerRadius )
        mob_damper = Rectangle (
            width = damperSize [ 0 ],
            height = damperSize [ 1 ],
            color = GREEN,
        ).move_to ( 
            UP * ( stringY + damperSize [ 1 ] / 2 ) + 
            LEFT * ( keyExtent [ 0 ] - pivot [ 0 ] ) 
        )
        
        def timeToAngle ( t_r ):
            return pressEasing ( t_r ) * maxAngle
        
        def timeToHammerState ( t_r ):
            if t_r < hammerUpRatio:
                t1 = t_r / hammerUpRatio
                return hammerUpEasing ( t1 )
            else: 
                t1 = ( 1 - t_r ) / ( 1 - hammerUpRatio )
                return hammerDownEasing ( t1 )
        
        linkerLength = stringY - pivot [ 1 ]
        def updateLinker ( mob ):
            angle = timeToAngle ( mob_var_t.get_value ( ) )
            stringLeftEnd = rotate_vector ( LEFT * keyExtent [ 0 ], -angle ) + pivot
            mob.put_start_and_end_on (
                stringLeftEnd,
                stringLeftEnd + UP * linkerLength,
            )
        
        def updateDamper ( mob ):
            angle = timeToAngle ( mob_var_t.get_value ( ) )
            damperCenter = ( 
                rotate_vector ( LEFT * keyExtent [ 0 ], -angle ) + 
                pivot + UP * ( linkerLength + damperSize [ 1 ] / 2 )
            )
            mob.move_to ( damperCenter )
        
        def updateHammer ( mob ):
            hammerState = timeToHammerState ( mob_var_tHammer.get_value ( ) )
            mob.move_to ( 
                pivot + LEFT * hammerPosition + 
                UP * ( 
                    hammerRadius + hammerState * 
                    ( linkerLength - 2 * hammerRadius ) 
                )
            )
        
        self.play ( Write ( mob_text_title ) )
        
        self.play (
            Create ( mob_key ),
            GrowFromPoint ( mob_triangle_pivot, pivot ),
            FadeIn ( mob_dot_pivot ),
            Create ( mob_string ),
            Create ( mob_hammer, run_time = 0.25 ),
            Succession (
                Create ( mob_damperLinker, run_time = 0.5 ),
                Create ( mob_damper, run_time = 0.25 ),
            ),
            run_time = 0.75,
        )
        
        mob_text_damper = Text ( "制音器", **textConfig )\
            .next_to ( mob_damper, UP, buff = 0.2 )
        mob_text_hammer = Text ( "琴槌", **textConfig )\
            .next_to ( mob_hammer, UP, buff = 0.2 )
        mob_text_key = Text ( "琴键", **textConfig )\
            .next_to ( mob_key, UP, buff = 0.2 )\
            .align_to ( mob_key, RIGHT )
        mob_text_string = Text ( "琴弦", **textConfig )\
            .next_to ( mob_string, UP, buff = 0.2 )\
            .align_to ( mob_string, RIGHT )
        mob_arrow_press = Arrow ( UP * 1.5, ORIGIN )\
            .next_to ( mob_text_key, LEFT, buff = 0.75 )\
            .align_to ( mob_key, DOWN )
        mob_text_press = Text ( "按键动作", **textConfig )\
            .next_to ( mob_arrow_press, UP, buff = 0.2 )
        
        self.play (
            Write ( mob_text_damper ),
            Write ( mob_text_hammer ),
            Write ( mob_text_key ),
            Write ( mob_text_string ),
            Create ( mob_arrow_press ),
            Write ( mob_text_press ),
            run_time = 0.5,
        )
        self.wait ( 2 )
        
        self.play (
            Unwrite ( mob_text_damper ),
            Unwrite ( mob_text_hammer ),
            Unwrite ( mob_text_key ),
            Unwrite ( mob_text_string ),
            Uncreate ( mob_arrow_press ),
            Unwrite ( mob_text_press ),
            run_time = 0.5,
        )
        
        mob_damperLinker.add_updater ( updateLinker )
        mob_damper.add_updater ( updateDamper )
        mob_hammer.add_updater ( updateHammer )
        
        for _ in range ( 10 ):
            mob_var_tHammer.set_value ( 0 )
            self.add_sound ( 
                DIR/"assets/sound/piano.wav",
                time_offset = wiggleDelay + pressTime * soundDelayRatio,
            )
            self.play (
                # 弦振动
                Succession (
                    Wait ( wiggleDelay ),
                    Wiggle ( 
                        mob_string, 
                        n_wiggles = wiggleTime * wiggleFreq, 
                        run_time = wiggleTime, 
                        scale_value = 1,
                        rotation_angle = PI / 90,
                        rate_func = linear,
                    ),
                ),
                # 琴槌运动
                mob_var_tHammer.animate ( 
                    run_time = pressTime * 2 + waitTime / 2, 
                    rate_func = linear 
                ).set_value ( 1 ),
                # 按键
                Succession (
                    AnimationGroup (
                        Rotate ( 
                            mob_key, 
                            angle = -maxAngle, 
                            about_point = pivot, 
                            rate_func = pressEasing,
                            run_time = pressTime,
                        ),
                        mob_var_t.animate ( run_time = pressTime, rate_func = linear )\
                            .set_value ( 1 ),
                    ),
                    AnimationGroup (
                        Rotate ( 
                            mob_key, 
                            angle = maxAngle, 
                            about_point = pivot, 
                            rate_func = pressEasing,
                            run_time = pressTime,
                        ),
                        mob_var_t.animate ( run_time = pressTime, rate_func = linear )\
                            .set_value ( 0 ),
                    ),
                    Wait ( waitTime ),
                )
            )

class StringInstrumentHarmonicScene ( Scene ):
    def construct ( self ):
        # 参考：https://www.bilibili.com/video/BV1XM4m1m7KP
        self.camera.background_color = "#282c34"
        
        stringLength = 12
        stringY = 0.125
        amp = 1.25
        period = 1
        nPeriods = 2
        runTime1 = period * ( nPeriods + 0.25 )
        stringLeft = LEFT * ( stringLength / 2 )
        stringRight = RIGHT * ( stringLength / 2 )
        ringPosition = Q ( 3, 5 )
        ringX = ( float ( ringPosition ) - 0.5 ) * stringLength
        k1 = ringPosition.denominator
        k2 = k1 - 1
        
        mob_text_title = Text ( 
                "弦乐器的“泛音”演奏技巧", 
                **(textConfig | {"font_size": 64}) 
        ).to_corner ( UL )
        
        self.play ( Write ( mob_text_title ), run_time = 1 )
        
        mob_seg_string = Line ( stringLeft, stringRight )\
            .shift ( UP * stringY )
        mob_dot_stringLeft = Dot ( stringLeft, radius = 0.06 )\
            .shift ( UP * stringY )
        mob_dot_stringRight = Dot ( stringRight, radius = 0.06 )\
            .shift ( UP * stringY )
        mob_dot_ring = Circle ( 0.1, color = YELLOW )\
            .move_to ( stringLeft )\
            .shift ( UP * stringY )
        
        self.play (
            FadeIn ( mob_dot_stringLeft, mob_dot_stringRight ),
            Create ( mob_seg_string ),
        )
        self.add ( mob_dot_ring )
        self.play (
            mob_dot_ring.animate ( run_time = 1 )\
                .shift ( RIGHT * float ( ringPosition * stringLength ) ),
        )
        self.play ( Flash ( mob_dot_ring ) )
        
        mob_arrow_ring = Arrow ( ORIGIN, UP * 1.5 )\
            .next_to ( mob_dot_ring, DOWN, buff = 0.2 )
        mob_tex_x0 = MathTex ( r"x_0", **( latexConfig | {"font_size": 40} ) )\
            .next_to ( mob_dot_ring, UP, buff = 0.2 )
        mob_text_note = Paragraph ( 
            "添加小环", "不改变有效振动弦长",
            **textConfig,
            line_spacing = 0.75,
            alignment = "center"
        ).next_to ( mob_arrow_ring, DOWN, buff = 0.3 )
        
        self.play ( 
            Succession ( 
                Create ( mob_arrow_ring ), 
                Write ( mob_text_note ),
                FadeIn ( mob_tex_x0, run_time = 0.5 )
            ),
            run_time = 1,
        )
        self.wait ( 1 )  
        self.play ( FadeOut ( mob_text_note ), run_time = 0.5 )
        
        mob_text_note = Paragraph ( 
            "但因为小环抑制振动",
            "此点必须成为波节", 
            **textConfig,
            line_spacing = 0.75,
            alignment = "center"
        ).next_to ( mob_arrow_ring, DOWN, buff = 0.3 )
        
        self.play ( FadeIn ( mob_text_note ), run_time = 0.5 )
        self.wait ( 1 )
        self.play ( 
            FadeOut ( mob_text_note, mob_tex_x0 ), 
            Uncreate ( mob_arrow_ring ),
            run_time = 0.5 
        )
        
        # 创建波形
        
        mob_var_t = ValueTracker ( 0 )
        mob_curve_wave = mob_seg_string.copy ( )\
            .set_stroke ( color = RED ) 
        
        def makeStringUpdater ( k ):
            def createString ( mob ):
                t = mob_var_t.get_value ( )
                mob.become ( 
                    FunctionGraph (
                        lambda x: ( 
                            amp * np.sin ( PI * k * x / stringLength ) * 
                            np.sin ( TAU * t ) 
                        ),
                        x_range = [ 0, stringLength ],
                        color = RED,
                    ).shift ( ( -stringLength / 2, stringY, 0 ) ) 
                )
            return createString
        
        # 展示以固定点为波节的驻波的可行性
        
        mob_text_ok = Text ( "OK", **( textConfig | {"font_size": 48} ) )
        mob_text_ok = VGroup ( 
            mob_text_ok, 
            SurroundingRectangle ( 
                mob_text_ok, buff = 0.2,
                color = WHITE, 
            ) 
        ).to_corner ( DL ).shift ( UP * 0.8 )
        mob_text_note = Text ( 
            "以固定点为波节的驻波可形成", 
            **( textConfig | {"font_size": 32} ) 
        ).next_to ( mob_text_ok, RIGHT, buff = 0.5 )
            
        self.play (
            mob_seg_string.animate.set_stroke ( opacity = 0.5 ),
            FadeIn ( mob_curve_wave ),
            run_time = 0.25,
        )
        mob_curve_wave.add_updater ( makeStringUpdater ( k1 ) )
        self.play ( 
            mob_var_t.animate ( run_time = runTime1, rate_func = smoothStart ( 0.1 ) )\
                .set_value ( nPeriods + 0.25 ) 
        )
        self.add ( mob_text_ok )
        self.play ( 
            Flash ( mob_dot_ring ), 
            Write ( mob_text_note, run_time = 0.5 ) 
        )
        self.wait ( 2 )
        
        # 展示不以固定点为波节的驻波不可行
        
        mob_text_ng = Text ( "NG", **( textConfig | {"font_size": 48} ) )
        mob_text_ng = VGroup ( 
            mob_text_ng, 
            SurroundingRectangle ( 
                mob_text_ng, buff = 0.2,
                color = WHITE, 
            ) 
        ).to_corner ( DL ).shift ( UP * 0.8 )
        
        self.play ( 
            FadeOut ( 
                mob_text_ok, mob_text_note, 
                run_time = 0.5, 
                rate_func = rate_functions.ease_in_cubic 
            ),
            mob_var_t.animate ( run_time = 0.5, rate_func = rate_functions.ease_in_cubic )\
                .increment_value ( 0.25 ) 
        )
        
        mob_text_note = Text ( 
            "不以固定点为波节的驻波被抑制，无法形成", 
            **( textConfig | {"font_size": 32} ) 
        ).next_to ( mob_text_ng, RIGHT, buff = 0.5 )
        
        mob_curve_wave.clear_updaters ( )
        mob_var_t.set_value ( 0 )
        mob_curve_wave.add_updater ( makeStringUpdater ( k2 ) )
        
        pointOnStringY = stringY + amp * np.sin ( PI * k2 * float ( ringPosition ) )
        mob_seg_ringToString = Line (
            ( ringX, stringY, 0 ),
            ( ringX, pointOnStringY, 0 )
        )
        mob_dot_pointOnString = Dot ( ( ringX, pointOnStringY, 0 ), radius = 0.06 )
        self.play (
            mob_var_t.animate ( run_time = 0.5, rate_func = rate_functions.ease_out_cubic )\
                .set_value ( 0.25 ),
            Create ( mob_seg_ringToString, run_time = 0.5 ),
            FadeIn ( mob_dot_pointOnString, run_time = 0.5 ),
        )
        mob_curve_wave.clear_updaters ( )
        
        self.add ( mob_text_ng )
        for _ in range ( 4 ):
            self.play (  
                mob_curve_wave.animate ( run_time = 0.01 )\
                        .set_stroke ( opacity = 0.5 )
            )
            self.wait ( 0.09 )
            self.play (  
                mob_curve_wave.animate ( run_time = 0.01 )\
                        .set_stroke ( opacity = 1 )
            )
            self.wait ( 0.09 )
        self.play ( 
            Write ( mob_text_note ), 
            VGroup ( 
                mob_curve_wave, 
                mob_dot_pointOnString, 
                mob_seg_ringToString,
            ).animate.set_stroke ( opacity = 0.5 ),
            run_time = 1,
        )
        self.wait ( 1.5 )
        
        self.play (
            FadeOut ( 
                mob_seg_ringToString, mob_dot_pointOnString,
                mob_curve_wave, mob_text_ng, mob_text_note,
            ),
        )
        
        # 展示固定点必须是有理点
        
        mob_text_note = Text ( 
            "单弦驻波的波节一定位于弦上的有理分点", 
            **( textConfig | {"font_size": 32} ) 
        ).to_corner ( DL ).shift ( UP * 0.8 )
            
        mob_tex_rational = MathTex (
            r"x_0 = \frac{n}{m} \in \mathbb{Q} \cap (0, 1)", 
            **( latexConfig | {"font_size": 40} )
        ).next_to ( mob_dot_ring, DOWN, buff = 0.2 )
        mob_tex_coprime = MathTex (
            r"\gcd (m, n) = 1",
            **( latexConfig | {"font_size": 40} )
        ).next_to ( mob_tex_rational, DOWN, buff = 0.2 )
        self.play ( 
            Write ( mob_text_note, run_time = 1 ),
            Succession (
                Write ( mob_tex_rational, run_time = 0.3 ),
                Write ( mob_tex_coprime, run_time = 0.3 ),
            )
        )
        
        layers = 12
        mob_vg_rationalBars = VGroup ( )
        
        for m in range ( 1, layers + 1 ):
            for n in range ( m + 1 ):
                if np.gcd ( m, n ) == 1:
                    lineX = ( n / m - 0.5 ) * stringLength
                    lineHeight = amp / m
                    mob_vg_rationalBars.add (
                        Line (
                            ( lineX, lineHeight, 0 ),
                            ( lineX, -lineHeight, 0 ),
                            color = BLUE,
                        ).shift ( UP * stringY )\
                            .set_stroke ( 
                                opacity = np.pow ( 1 / m, 0.25 ) * 0.75,
                                width = max ( 24 * np.sqrt ( 1 / m ), 4 ),
                            )
                    )
                    
        self.play ( 
            Create ( 
                mob_vg_rationalBars, 
                run_time = 1.5 
            ),  
            VGroup ( mob_tex_rational, mob_tex_coprime ).animate ( run_time = 1 )\
                .shift ( DOWN * 0.5 )
        )
        self.wait ( 3 )
        
        mob_text_note2 = Tex ( 
            "小环放在 $x_0$ 处时，可行的波段数为 $x_0$ 的最小分母 $m$ 的倍数", 
            **(latexConfig | {"font_size": 40}),
        ).to_corner ( DL ).shift ( UP * 0.8 )
        
        mob_vg_rationalBars.invert ( )
        mob_tex_kValue = MathTex (
            r"k = m",
            **( latexConfig | {"font_size": 40} )
        ).next_to ( mob_text_note2, UP, buff = 0.3 )\
            .align_to ( mob_text_note2, LEFT )
        
        # 展示波段数为 m 倍数的驻波 
        
        ringPosition = Q ( 2, 3 )
        ringX = ( float ( ringPosition ) - 0.5 ) * stringLength
        k1 = ringPosition.denominator
        
        self.play (
            Write ( mob_text_note2, run_time = 1 ),
            mob_text_note.animate ( run_time = 0.75 )\
                .next_to ( mob_text_title, DOWN, buff = 0.4 )\
                .align_to ( mob_text_title, LEFT ),
            Uncreate ( mob_vg_rationalBars, run_time = 1 ),
        )
        self.play (
            FadeOut ( mob_tex_rational, mob_tex_coprime ),
            VGroup (
                mob_seg_string, 
                mob_dot_stringLeft, mob_dot_stringRight, 
            ).animate.shift ( DOWN * 0.2 ),
            mob_dot_ring.animate\
                .shift ( DOWN * 0.2 )\
                .set_coord ( ringX, 0 ),
            run_time = 0.5,
        )
        
        stringY -= 0.2
        
        maxMultiples = 4
        mob_curve_wave = FunctionGraph (
            lambda x: amp * np.sin ( PI * k1 * x / stringLength ),
            x_range = [ 0, stringLength ],
            color = RED,
        ).shift ( ( -stringLength / 2, stringY, 0 ) )
        mob_curve_invWave = FunctionGraph (
            lambda x: -amp * np.sin ( PI * k1 * x / stringLength ),
            x_range = [ 0, stringLength ],
            color = RED,
        ).shift ( ( -stringLength / 2, stringY, 0 ) )\
            .set_stroke ( opacity = 0.5 )
        
        self.play (
            Create ( mob_curve_wave, run_time = 1 ),
            Create ( mob_curve_invWave, run_time = 1 ),
            Write ( mob_tex_kValue, run_time = 0.5 ),
        )
        self.wait ( 1 )
        
        for i in range ( 2, maxMultiples + 1 ):
            self.play (
                Transform ( 
                    mob_curve_wave, 
                    FunctionGraph (
                        lambda x: amp * np.sin ( PI * i * k1 * x / stringLength ),
                        x_range = [ 0, stringLength ],
                        color = RED,
                    ).shift ( ( -stringLength / 2, stringY, 0 ) ),
                    run_time = 0.75,
                ),
                Transform ( 
                    mob_curve_invWave, 
                    FunctionGraph (
                        lambda x: -amp * np.sin ( PI * i * k1 * x / stringLength ),
                        x_range = [ 0, stringLength ],
                        color = RED,
                    ).shift ( ( -stringLength / 2, stringY, 0 ) )\
                        .set_stroke ( opacity = 0.5 ),
                    run_time = 0.75,
                ),
                Transform ( 
                    mob_tex_kValue, 
                    MathTex (
                        rf"k = {i}m",
                        **( latexConfig | {"font_size": 40} )
                    ).next_to ( mob_text_note2, UP, buff = 0.3 )\
                        .align_to ( mob_text_note2, LEFT ),
                    run_time = 0.5,
                ),
            )
            self.wait ( 1 )
            
        self.wait ( 1 )
        
        # 展示振动模式在有无固定点时的变化
        
        ringPosition = Q ( 1, 2 )
        ringX = ( float ( ringPosition ) - 0.5 ) * stringLength
        k1 = ringPosition.denominator
        
        _, exampleWaveform = analyzeSoundFile (
            DIR/"assets/sound/violin.wav",
            **analyzeConfig,
        )
        n = 6
        harmonicWaveform = exampleWaveform | k1
        cutoffWaveform = exampleWaveform [ :n ]
        cutoffHarmonicWaveform = cutoffWaveform | k1
        
        mob_seg_lineAtRing = Line (
            ( ringX, amp, 0 ), ( ringX, -amp, 0 ),
        ).shift ( UP * stringY )
        mob_dot_pointAtRing = Dot ( radius = 0.07 )
        
        self.play (
            Uncreate ( mob_curve_wave ),
            Uncreate ( mob_curve_invWave ),
            FadeOut ( mob_tex_kValue, mob_text_note, mob_text_note2 ),
            mob_dot_ring.animate\
                .set_coord ( ringX, 0 ).set_stroke ( opacity = 0.5 ),
            Create ( mob_seg_lineAtRing ),
            run_time = 0.5,
        )
        
        mob_text_note = Text ( 
            "无限制时的弦振动，所有质点都能上下运动", 
            **( textConfig ) 
        ).to_corner ( DL ).shift ( UP * 0.8 )
        mob_tex_summedWave = MathTex (
            r"y(x, t) = ",
            r"\sum_{k=1}^{+\infty}",
            r"A_k",
            r"\sin (\pi kx)",
            r"\sin (2\pi k t + \varphi_k)",
            **( latexConfig | {"font_size": 36} ),
        ).next_to ( mob_text_title, DOWN, buff = 0.25 )\
            .align_to ( mob_text_title, LEFT )
        
        mob_var_t.set_value ( 0 )
        
        def updatePointAtRing ( mob ):
            t = mob_var_t.get_value ( )
            y = amp * exampleWaveform.calcStandingWave ( 
                float ( ringPosition ), t
            )
            mob.set_coord ( y + stringY, 1 )
        
        def createStringCurve ( ):
            t = mob_var_t.get_value ( )
            return FunctionGraph (
                lambda x: amp * exampleWaveform.calcStandingWave ( x / stringLength, t ),
                x_range = [ 0, stringLength ],
                color = RED,
            ).shift ( stringLeft + UP * stringY )
        
        def createSineCurve ( k ):
            t = mob_var_t.get_value ( )
            return FunctionGraph (
                lambda x: ( 
                    cutoffWaveform.calcStandingWaveComponent ( 
                        k, x / stringLength, t
                    ) * amp
                ),
                x_range = [ 0, stringLength ],
                color = RED,
            ).shift ( stringLeft + UP * stringY )\
                .set_stroke ( opacity = 0.5 )
        
        def makeSineUpdater ( k ):
            return lambda: createSineCurve ( k )
        
        def createHarmonicCurve ( ):
            t = mob_var_t.get_value ( )
            return FunctionGraph (
                lambda x: ( 
                    amp * harmonicWaveform.calcStandingWave ( 
                        x / stringLength * k1, t * k1
                    ) 
                ),
                x_range = [ 0, stringLength ],
                color = RED,
            ).shift ( stringLeft + UP * stringY )
        
        def createHarmonicSineCurve ( k ):
            t = mob_var_t.get_value ( )
            return FunctionGraph (
                lambda x: ( 
                    cutoffHarmonicWaveform.calcStandingWaveComponent ( 
                        k, x / stringLength * k1, t * k1
                    ) * amp
                ),
                x_range = [ 0, stringLength ],
                color = RED,
            ).shift ( stringLeft + UP * stringY )\
                .set_stroke ( opacity = 0.5 )
        
        def makeHarmonicSineUpdater ( k ):
            return lambda: createHarmonicSineCurve ( k )
        
        mob_dot_pointAtRing.add_updater ( updatePointAtRing )
        mob_curve_wave = always_redraw ( createStringCurve )
        mob_vg_sines = VGroup ( )
        
        for k in range ( 1, len ( cutoffWaveform ) + 1 ):
            mob_curve_sine = always_redraw ( makeSineUpdater ( k ) )
            mob_vg_sines.add ( mob_curve_sine )
        
        period = 2
        nPeriods = 5
        runTime = nPeriods * period
        
        self.play (
            Create ( mob_curve_wave ),
            Create ( mob_vg_sines ),
            FadeIn ( mob_dot_pointAtRing ),
            Write ( mob_text_note ),
            Write ( mob_tex_summedWave ),
            run_time = 1,
        )
        self.play (
            mob_var_t.animate ( run_time = runTime, rate_func = smoothBoth ( 0.1 ) )\
                .set_value ( nPeriods ) 
        )
        self.play (
            mob_dot_ring.animate.set_stroke ( opacity = 1 ),
            FadeOut ( mob_curve_wave, mob_dot_pointAtRing, mob_text_note ),
            Uncreate ( mob_seg_lineAtRing ),
            Uncreate ( mob_vg_sines, run_time = 0.75 ),
            run_time = 0.5,
        )
        
        mob_text_note = Text ( 
            "有限制时的弦振动，固定点成为波节，保持静止", 
            **( textConfig | {"font_size": 32} ) 
        ).to_corner ( DL ).shift ( UP * 0.8 )
        mob_vg_sines = VGroup ( )
        
        for k in range ( 1, len ( cutoffHarmonicWaveform ) + 1 ):
            mob_curve_sine = always_redraw ( makeHarmonicSineUpdater ( k ) )
            mob_vg_sines.add ( mob_curve_sine )
        
        mob_curve_wave.clear_updaters ( )
        mob_dot_pointAtRing.clear_updaters ( )
        mob_var_t.set_value ( 0 )
        mob_curve_wave = always_redraw ( createHarmonicCurve )
        
        self.play (
            Create ( mob_curve_wave, run_time = 1 ),
            Create ( mob_vg_sines, run_time = 1 ),
            Write ( mob_text_note, run_time = 1 ),
            Transform ( 
                mob_tex_summedWave, 
                MathTex (
                    r"y(x, t) = ",
                    r"\sum_{k \in m\mathbb{N}^{*}}",
                    r"A_k",
                    r"\sin (\pi kx)",
                    r"\sin (2\pi k t + \varphi_k)",
                    **( latexConfig | {"font_size": 36} )
                ).next_to ( mob_text_title, DOWN, buff = 0.4 )\
                    .align_to ( mob_text_title, LEFT ), 
                run_time = 0.5,
            ),
            Flash ( mob_dot_ring ),
        )
        self.play (
            mob_var_t.animate ( run_time = runTime, rate_func = smoothBoth ( 0.1 ) )\
                .set_value ( nPeriods ) 
        )
        
        self.play (
            Uncreate ( mob_curve_wave, run_time = 1 ),
            Uncreate ( mob_vg_sines, run_time = 0.75 ),
            FadeOut ( 
                mob_seg_string, 
                mob_dot_stringLeft, mob_dot_stringRight,
                mob_dot_ring,
                mob_text_note,
                mob_tex_summedWave,
            ),
        )
        
        # 展示常规音色与泛音音色的频谱关系
        
        rx = config [ "frame_x_radius" ]
        ry = config [ "frame_y_radius" ]
        space = 0.75
        ySpace = 0.4
        w = ( 2 * rx - 3 * space ) / 2
        h1 = 2.9
        h2 = h1
        phaseAreaRatio = 0.3
        dividerX = -rx + space
        dividerY = ry - ySpace - h1 * ( 1 - phaseAreaRatio )
        timelineY = ry - ySpace * 2 - h1 - h2 / 2
        dividerLeft = np.array (( dividerX, dividerY, 0 ))
        dividerRight = dividerLeft + RIGHT * w
        timelineLeft = np.array (( dividerX, timelineY, 0 ))
        timelineRight = timelineLeft + RIGHT * w
        nHarmonics = 10
        barSpace = 0.15
        barWidth = ( w - ( nHarmonics + 1 ) * barSpace ) / nHarmonics
        barBuff = 0.2
        waveformBuff = 0.4
        waveformAmp = h2 / 2 - waveformBuff
        ampBarMaxHeight = h1 * ( 1 - phaseAreaRatio ) - barBuff
        phaseBarMaxHeight = h1 * phaseAreaRatio - barBuff
        
        mob_rect_spectrumArea1 = Rectangle ( width = w, height = h1 )\
            .to_corner ( UL, buff = space ).shift ( UP * ( space - ySpace ) )
        mob_rect_waveformArea1 = Rectangle ( width = w, height = h2 )\
            .next_to ( mob_rect_spectrumArea1, DOWN, buff = ySpace )
        mob_line_divider1 = Line ( dividerLeft, dividerRight )\
            .set_stroke ( opacity = 0.5 )
        mob_line_timeline1 = Line ( timelineLeft, timelineRight )\
            .set_stroke ( opacity = 0.5 )
        mob_text_originalSpectrum = Text ( "原始频谱", **textConfig )\
            .align_to ( mob_rect_spectrumArea1, UR )\
            .shift ( ( -0.25, -0.25, 0 ) )
        mob_text_originalWaveform = Text ( "原始波形", **textConfig )\
            .align_to ( mob_rect_waveformArea1, UR )\
            .shift ( ( -0.25, -0.25, 0 ) )
        mob_text_newSpectrum = Text ( "新频谱", **textConfig )\
            .align_to ( mob_rect_spectrumArea1, UR )\
            .shift ( ( w + space - 0.25, -0.25, 0 ) )
        mob_text_newWaveform = Text ( "新波形", **textConfig )\
            .align_to ( mob_rect_waveformArea1, UR )\
            .shift ( ( w + space - 0.25, -0.25, 0 ) )
        
        harmonics = np.array ( [ exampleWaveform [ k ] for k in range ( 1, nHarmonics + 1 ) ] )
        amps = np.abs ( harmonics )
        phases = np.angle ( harmonics )
        phases [ 0 ] = 0
        phases [ phases < 0 ] += TAU
        maxAmp = np.max ( amps )
        
        newHarmonics = np.array ( [ harmonicWaveform [ k ] for k in range ( 1, nHarmonics // k1 + 1 ) ] )
        newAmps = np.abs ( newHarmonics )
        newPhases = np.angle ( newHarmonics )
        newPhases [ 0 ] = 0
        newPhases [ newPhases < 0 ] += TAU
        newMaxAmp = np.max ( newAmps )
        
        cutoffWaveform = exampleWaveform [ ::k1 ]
        
        mob_vg_spectrumAmp1 = VGroup ( )
        mob_vg_spectrumPhase1 = VGroup ( )
        mob_vg_newSpectrumAmp = VGroup ( )
        mob_vg_newSpectrumPhase = VGroup ( )
        
        waveformMax = findMax ( exampleWaveform )
        newWaveformMax = findMax ( harmonicWaveform )
        
        mob_curve_waveform = FunctionGraph (
            lambda t: exampleWaveform ( t / w ) / waveformMax * waveformAmp,
            color = PURE_GREEN,
            x_range = [ 0, w ],
        ).shift ( timelineLeft )
        mob_curve_harmonicWaveform = FunctionGraph (
            lambda t: cutoffWaveform ( t / w ) / newWaveformMax * waveformAmp,
            color = PURE_GREEN,
            x_range = [ 0, w ],
        ).shift ( timelineLeft + ( w + space, 0, 0 ) )
        mob_curve_harmonicWaveformOnePeriod = FunctionGraph (
            lambda t: harmonicWaveform ( t / w ) / newWaveformMax * waveformAmp,
            color = PURE_GREEN,
            x_range = [ 0, w ],
        ).shift ( timelineLeft + ( w + space, 0, 0 ) )
        
        for i, ( a, ph ) in enumerate ( zip ( amps, phases ) ):
            ampBarHeight = a / maxAmp * ampBarMaxHeight
            phaseBarHeight = ph / TAU * phaseBarMaxHeight
            barX = dividerX + ( i + 1 ) * barSpace + i * barWidth
            mob_vg_spectrumAmp1.add (
                Polygon (
                    ( barX, dividerY, 0 ),
                    ( barX + barWidth, dividerY, 0 ),
                    ( barX + barWidth, dividerY + ampBarHeight, 0 ),
                    ( barX, dividerY + ampBarHeight, 0 ),
                    color = BLUE,
                    fill_color = BLUE,
                    fill_opacity = 0.5,
                ),
            )
            mob_vg_spectrumPhase1.add (
                Polygon (
                    ( barX, dividerY, 0 ),
                    ( barX + barWidth, dividerY, 0 ),
                    ( barX + barWidth, dividerY - phaseBarHeight, 0 ),
                    ( barX, dividerY - phaseBarHeight, 0 ),
                    color = PURPLE,
                    fill_color = PURPLE,
                    fill_opacity = 0.5,
                ),
            )
        
        for i, ( a, ph ) in enumerate ( zip ( newAmps, newPhases ) ):
            ampBarHeight = a / newMaxAmp * ampBarMaxHeight
            phaseBarHeight = ph / TAU * phaseBarMaxHeight
            barX = dividerX + ( i + 1 ) * barSpace + i * barWidth + w + space
            mob_vg_newSpectrumAmp.add (
                Polygon (
                    ( barX, dividerY, 0 ),
                    ( barX + barWidth, dividerY, 0 ),
                    ( barX + barWidth, dividerY + ampBarHeight, 0 ),
                    ( barX, dividerY + ampBarHeight, 0 ),
                    color = BLUE,
                    fill_color = BLUE,
                    fill_opacity = 0.5,
                ),
            )
            mob_vg_newSpectrumPhase.add (
                Polygon (
                    ( barX, dividerY, 0 ),
                    ( barX + barWidth, dividerY, 0 ),
                    ( barX + barWidth, dividerY - phaseBarHeight, 0 ),
                    ( barX, dividerY - phaseBarHeight, 0 ),
                    color = PURPLE,
                    fill_color = PURPLE,
                    fill_opacity = 0.5,
                ),
            )
        
        self.play (
            FadeOut ( mob_text_title ),
            FadeIn ( 
                mob_rect_spectrumArea1, mob_rect_waveformArea1,
                mob_text_originalSpectrum, mob_text_originalWaveform,
            ),
            Create ( mob_line_divider1 ),
            Create ( mob_line_timeline1 ),
            run_time = 1,
        )
        self.play (
            Create ( mob_curve_waveform ),
            Create ( mob_vg_spectrumAmp1 ),
            Create ( mob_vg_spectrumPhase1 ),
            run_time = 0.5,
        )
        self.wait ( 0.5 )
        
        mob_rect_spectrumArea2 = mob_rect_spectrumArea1.copy ( )
        mob_rect_waveformArea2 = mob_rect_waveformArea1.copy ( )
        mob_line_divider2 = mob_line_divider1.copy ( )
        mob_line_timeline2 = mob_line_timeline1.copy ( )
        mob_vg_spectrumAmp2 = mob_vg_spectrumAmp1.copy ( )
        mob_vg_spectrumPhase2 = mob_vg_spectrumPhase1.copy ( )
        mob_curve_waveform2 = mob_curve_waveform.copy ( )
        
        mob_vg_graphs2 = VGroup ( 
            mob_rect_spectrumArea2,
            mob_rect_waveformArea2,
            mob_line_divider2,
            mob_line_timeline2,
            mob_vg_spectrumAmp2,
            mob_vg_spectrumPhase2,
            mob_curve_waveform2,
        )
        
        self.add ( mob_vg_graphs2 )
        self.play (
            mob_vg_graphs2.animate\
                .set_coord ( ( space + w ) / 2, 0 ),
            run_time = 1,
        )
        
        animationsToPlay = [ ]
        animationsToPlay2 = [ ]
        for i, ( mob_ampBar, mob_phaseBar ) in enumerate ( 
                zip ( mob_vg_spectrumAmp2, mob_vg_spectrumPhase2 ) 
        ):
            k = i + 1
            if k % k1 != 0:
                animationsToPlay.append (
                    AnimationGroup (
                        Uncreate ( mob_ampBar ),
                        Uncreate ( mob_phaseBar ),
                    ),
                )
            else:
                j = k // k1 - 1
                animationsToPlay2.extend ((
                    Transform ( mob_ampBar, mob_vg_newSpectrumAmp [ j ] ),
                    Transform ( mob_phaseBar, mob_vg_newSpectrumPhase [ j ] ),
                ))
        self.play (
            LaggedStart ( *animationsToPlay, lag_ratio = 0.25 ),
            Transform ( mob_curve_waveform2, mob_curve_harmonicWaveform ),
            FadeIn ( mob_text_newSpectrum, mob_text_newWaveform ),
            run_time = 1,
        )
        self.wait ( 1.5 )
        self.play ( 
            *animationsToPlay2, 
            Transform ( mob_curve_waveform2, mob_curve_harmonicWaveformOnePeriod ),
            run_time = 1 
        )
        self.wait ( 2 )
        
class SubtitleScene ( Scene ):
    def construct ( self ):
        data = json.loads ( 
            ( DIR/"assets/sub.json" )\
                .read_text ( encoding = "utf-8" ) 
                # 有中文一定要用 utf-8 编码，否则会报错
        )
        
        lastStart = lastEnd = 0
        mob_subtitle = None
        
        for i, line in enumerate ( data ):
            start = line.get ( "startTime" )
            end = line.get ( "endTime" )
            if lastEnd is None:
                lastEnd = start
            print ( lastEnd - lastStart )
            self.wait ( ( lastEnd - lastStart ) / 1000 )
            
            if mob_subtitle is not None:
                self.remove ( mob_subtitle )
            self.wait ( ( start - lastEnd ) / 1000 )
                
            print ( f"Line {i}: {line [ "content" ]}" )
            
            mob_subtitle = Tex ( line [ "content" ], **latexConfig )\
                .to_corner ( DOWN, buff = 0.25 )
            mob_subtitleBg = SurroundingRectangle ( mob_subtitle )\
                .set_fill ( color = BLACK, opacity = 0.5 )\
                .set_stroke ( width = 0, opacity = 0 )
            mob_subtitle = VGroup ( mob_subtitleBg, mob_subtitle )
            
            self.add ( mob_subtitle )
            
            lastStart, lastEnd = start, end
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
###################################################
###################################################
###################################################
###################################################
# ###################################################
###################################################
# ###################################################
###################################################




# class Test3DScene ( ThreeDScene ):
#     def construct ( self ):
#         # self.set_camera_orientation ( phi = PI / 3, theta = -PI / 3 )
#         # self.add ( ThreeDAxes () )
#         self.add ( FunctionGraph ( lambda x: np.sin ( x ) ) )
#         mob_var_theta, mob_var_phi, mob_var_gamma = (
#             self.camera.theta_tracker,
#             self.camera.phi_tracker,
#             self.camera.gamma_tracker,
#         )
#         self.play (
#             mob_var_phi.animate.set_value ( -PI / 6 ),
#         )
#         self.play (
#             mob_var_theta.animate.increment_value ( -PI / 3 ),
#         )
#         self.play (
#             mob_var_gamma.animate.increment_value ( -64 * DEGREES ),
#         )
#         self.wait ( 2 )
#         print (
#             self.camera.theta_tracker.get_value ( ),
#             self.camera.phi_tracker.get_value ( ),
#             self.camera.gamma_tracker.get_value ( ),
#         )




# ###################################################
###################################################
###################################################
###################################################
###################################################
###################################################
# ###################################################
###################################################
# ###################################################
############################











# ###################################################
###################################################
###################################################
###################################################
###################################################
###################################################
# ###################################################
###################################################
# ###################################################
###################################################