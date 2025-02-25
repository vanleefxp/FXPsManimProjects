from collections.abc import Mapping
import sys
from pathlib import Path
from fractions import Fraction as Q
import itertools as it
import operator as op

from manim import *
import manim.utils.rate_functions as rf   
import numpy as np
import pyrsistent as pyr

DIR = Path ( __file__ ).parent if "__file__" in locals ( ) else Path.cwd ( )
sys.path.insert ( 0, str ( DIR/".." ) )
from public import *

config.background_color = "#282c34"
musicFont = "Chaconne Ex"
keyboardConfig = pyr.m (
    whiteWidth = 0.42,
    whiteHeight = 2.25,
    blackWidth = 0.21,
    blackHeight = 1.25,
)
staffConfig = pyr.m (
    staffLineThickness = 2,
    ledgerLineThickness = 3,
    musicFont = musicFont,
)
tipConfig = pyr.m (
    tip_shape = StealthTip, 
    tip_length = 0.2,
    tip_width = 0.1,
)

_noteNames = np.array (( "C", "D", "E", "F", "G", "A", "B" ))
_intervalQualityNames = pyr.pmap ( {
    -3: "倍减",
    -2: "减",
    -1: "小",
    0: "纯",
    1: "大",
    2: "增",
    3: "倍增",
} )
_intervalQualityLetters = pyr.pmap ( {
    -3: "dd",
    -2: "d",
    -1: "m",
    0: "P",
    1: "M",
    2: "A",
    3: "AA",
} )
_cnNumbers = pyr.pvector ([ "一", "二", "三", "四", "五", "六", "七", "八", "九" ])
_majorScale = np.sort ( np.arange ( -1, 6 ) * 7 % 12 )
_co5DegreeOrder = ( np.arange ( -1, 6 ) * 4 ) % 7
_co5DegreeArgs = np.argsort ( _co5DegreeOrder )
_noteNamesCo5Order = _noteNames [ _co5DegreeOrder ]

def _getAcciCountText ( acciCount: int ) -> str:
    if acciCount == 0: return r"0{\sh}/0{\fl}"
    elif acciCount > 0: return rf"{acciCount}{{\sh}}"
    else: return rf"{-acciCount}{{\fl}}"

@lru_cache
def _getAlteredDegrees ( acciCount: int ) -> np.ndarray:
    if acciCount > 0: alteredDegrees = np.arange ( 6 - acciCount, 6 ) * 4 % 7
    elif acciCount < 0: alteredDegrees = np.arange ( -1, -1 - acciCount ) * 4 % 7
    else: alteredDegrees = np.array ((), dtype = int )
    alteredDegrees.flags.writeable = False
    return alteredDegrees

@lru_cache
def _getKeyNoteNames ( acciCount: int ) -> np.ndarray:
    startDegree = acciCount * 4 % 7
    keyNoteNames = np.roll ( _noteNames, -startDegree ).astype ( "<U6" )
    alteredDegrees = _getAlteredDegrees ( acciCount )
    keyNoteNames [ alteredDegrees ] = ( 
        ( r"{\sh}" if acciCount > 0 else r"{\fl}" ) + 
        keyNoteNames [ alteredDegrees ]
    )
    return keyNoteNames

def _createNoteNameTexts ( 
        acciCount: int, 
        fs: float = 1.25,
        buff = 0.25,
        co5Order: bool = False,
) -> VGroup:
    mob_texts = VGroup ( )
    if co5Order:
        if acciCount > 0:
            for i in range ( acciCount ):
                mob_text = Tex ( 
                    r"{\sh}", _noteNamesCo5Order [ i ], 
                    **newLatexConfig ( fs = fs ) 
                )
                mob_text [ 1 ].set_color ( RED )
                mob_texts.add ( mob_text )
            for i in range ( acciCount, 7 ):
                mob_text = Tex ( 
                    "", _noteNamesCo5Order [ i ], 
                    **newLatexConfig ( fs = fs ) 
                )
                mob_texts.add ( mob_text )
        else:
            for i in range ( 7 + acciCount ):
                mob_text = Tex ( 
                    "", _noteNamesCo5Order [ i ], 
                    **newLatexConfig ( fs = fs ) 
                )
                mob_texts.add ( mob_text )
            for i in range ( 7 + acciCount, 7 ):
                mob_text = Tex ( 
                    r"{\fl}", _noteNamesCo5Order [ i ], 
                    **newLatexConfig ( fs = fs ) 
                )
                mob_text [ 1 ].set_color ( GREEN )
                mob_texts.add ( mob_text )
    else:
        alteredDegrees = _getAlteredDegrees ( acciCount )
        keyNoteNames = _getKeyNoteNames ( acciCount )
        for i in range ( 7 ):
            s = keyNoteNames [ i ]
            mob_text = Tex ( s [ :-1 ], s [ -1 ], **newLatexConfig ( fs = fs ) ) 
            if i in alteredDegrees:
                mob_text [ 1 ].set_color ( RED if acciCount > 0 else GREEN )
            mob_texts.add ( mob_text )
    mob_texts.arrange_in_grid ( 
        rows = 1, row_alignments = "u", 
        buff = buff,
    )
    return mob_texts

def _createKeyNameText ( 
        acciCount: int, 
        fs: float = 1.25,
        showAcciCount = False,
) -> Tex:
    keyNoteNames = _getKeyNoteNames ( acciCount )
    mob_text = Tex ( 
        (
            f"{ keyNoteNames [ 0 ] } 大调 "
            f"({ _getAcciCountText ( acciCount ) })"
            if showAcciCount
            else f"{ keyNoteNames [ 0 ] } 大调"
        ),
        **newLatexConfig ( fs = fs ),
    )
    return mob_text

@np.vectorize ( excluded = ( 1, ) )
def pitch2Freq ( pitch: float, a4Freq: float = 440 ) -> float:
    return a4Freq * 2 ** ( ( pitch - 69 ) / 12 )

def scaleDegree2Tone ( degree: int, tonic: int = 0 ) -> int:
    octave, octaveDegree = divmod ( degree, 7 )
    return _majorScale [ octaveDegree ] + tonic + octave * 12

def getIntervalQuality ( startDegree: int, degreeDiff: int ) -> int:
    toneDiff = ( 
        scaleDegree2Tone ( startDegree + degreeDiff ) - 
        scaleDegree2Tone ( startDegree )
    ) % 12
    standardToneDiff = _majorScale [ degreeDiff % 7 ]
    if degreeDiff in ( 0, 3, 4, 7 ):
        if toneDiff == standardToneDiff: return 0 # perfect
        elif toneDiff > standardToneDiff: 
            # augmented or multiply augmented
            return toneDiff - standardToneDiff + 1
        else:
            # diminished or multiply diminished
            return toneDiff - standardToneDiff - 1
    elif toneDiff >= standardToneDiff:
        # major, augmented or multiply augmented
        return toneDiff - standardToneDiff + 1
    else:
        # minor, diminished or multiply diminished
        return toneDiff - standardToneDiff

def getIntervalAbbr ( startDegree: int, degreeDiff: int ) -> str:
    quality = getIntervalQuality ( startDegree, degreeDiff )
    return f"{_intervalQualityLetters [ quality ]}{degreeDiff + 1}"

def getIntervalName ( startDegree: int, degreeDiff: int ) -> str:
    quality = getIntervalQuality ( startDegree, degreeDiff )
    return f"{_intervalQualityNames [ quality ]}{_cnNumbers [ degreeDiff ]}度"

class TestScene ( Scene ):
    def construct ( self ):
        mob_noteBlock = NoteBlock ( )
        self.add ( mob_noteBlock )
        self.play ( mob_noteBlock.animatePlay ( ) )
        self.wait ( 2 )  

class IntroScene ( Scene ):
    def construct ( self ):
        mob_textProvide = Text ( "提    供", **newTextConfig ( fs = 2, font = "FandolHei" ) )\
            .to_edge ( UP, buff = 0.75 )
            
        mob_manshiLogo = Tex ( "M", "athematic", "S", **newLatexConfig ( fs = 4 ) )\
            .next_to ( mob_textProvide, DOWN, buff = 1.25 )
        mob_manshiLogo [ 0 ].set_color ( BLUE_B )
        mob_manshiLogo [ -1 ].set_color ( MAROON_A )
        mob_fxpLogo = MathTex ( r"\mathbb{F}[x]_p", **newLatexConfig ( fs = 3 ) )\
            .next_to ( mob_manshiLogo, DOWN, buff = 1.25 )
            
        mob_manshiText = Text ( "漫士沉思录", color= YELLOW, **newTextConfig ( fs = 2.5 ) )
        mob_fxpText = Text ( "F.X.P. Presents", **newTextConfig ( fs = 2.5 ) )

        self.add ( mob_textProvide )
        self.play (
            DrawBorderThenFill ( mob_manshiLogo, run_time = 1 ),
        )
        
        manshiLogoCenter = mob_manshiLogo.get_center ( )
        letterMDisplace = np.array (( 0, 0.125, 0 ))
        letterSDisplace = np.array (( 0.4, -0.125, 0 ))
        
        self.play (
            FadeOut ( mob_manshiLogo [ 1 ] ),
            mob_manshiLogo [ 0 ].animate\
                .move_to ( letterMDisplace + manshiLogoCenter ),
            mob_manshiLogo [ -1 ].animate\
                .move_to ( letterSDisplace + manshiLogoCenter ),
            run_time = 0.5,
        )
        mob_manshiLogo.remove ( mob_manshiLogo [ 1 ] )
        manshiLogoCenter = mob_manshiLogo.get_center ( )
        
        VGroup ( mob_manshiLogo, mob_manshiText, mob_fxpLogo, mob_fxpText )\
            .arrange_in_grid ( cols = 2, buff = ( 1, 1 ) )\
            .move_to ( DOWN * 0.5 )
        manshiLogoTargetPoint = mob_manshiLogo.get_center ( )
        
        mob_manshiLogo.move_to ( manshiLogoCenter )
        self.play (
            mob_manshiLogo.animate\
                .move_to ( manshiLogoTargetPoint ),
            FadeIn ( 
                mob_manshiText, 
                mob_fxpLogo, 
                mob_fxpText, 
            ),
            run_time = 0.5,
        )
        
        self.wait ( 2 )

class FrequencyAndIntervalScene ( Scene ):
    def construct ( self ):
        clefType = "G"
        
        mob_keyboard = MultiOctavePianoKeyboard ( octaves = 4, **keyboardConfig )\
            .center ( ).to_edge ( UP, buff = 1.5 )
        mob_staff = Staff ( **staffConfig, staffLength = 35 )\
            .next_to ( mob_keyboard, DOWN, buff = 1.5 )\
            .align_to ( mob_keyboard, LEFT )
        
        staffPosition = mob_staff.get_center ( )
        freqTextPosition = staffPosition.copy ( )
        noteNameTextPosition = staffPosition.copy ( )
        noteNameTextPosition [ 0 ] = 2
        freqTextPosition [ 0 ] = 4.5
        
        mob_clef = mob_staff.createClef ( clefType )\
            .setHpos ( 2 )
        
        self.play (
            FadeIn (
                mob_keyboard, mob_staff,
                run_time = 1,
            )
        )
        
        mask = np.array (( 0, -1, 1, -1, 2, 3, -1, 4, -1, 5, -1, 6 ))

        def animatePitch ( tone: int, acciPref: int = 1 ):
            octave, octaveTone = divmod ( tone, 12 )
            acciPref = 1 if acciPref >= 0 else -1
            midiNote = tone + 60
            freq = pitch2Freq ( midiNote )
            
            octaveScaleDegree = mask [ octaveTone ]
            acci = None
            if octaveScaleDegree < 0:
                octaveScaleDegree = mask [ octaveTone - acciPref ]
                acci = acciPref
            scaleDegree = octaveScaleDegree + octave * 7
            
            mob_note = mob_staff.createNote ( 
                scaleDegree - 6, 
                noteheadType = "whole",
                accidental = acci,
                add = False,
            ).setHpos ( 20 )
            noteNameText = f"{_noteNames [ octaveScaleDegree ]}$_{{{octave + 4}}}$"
            if acci is not None:
                if acci > 0: noteNameText = r"{\sh}" + noteNameText
                if acci < 0: noteNameText = r"{\fl}" + noteNameText
            mob_noteNameText = Tex (
                noteNameText,
                **newLatexConfig ( fs = 1.5 ),
            ).move_to ( noteNameTextPosition )
            mob_freqText = Text ( f"{freq:.2f} Hz", **newTextConfig ( fs = 1.5 ) )\
                .move_to ( freqTextPosition )
            addMidi ( self, midiNote )
            self.add ( mob_note, mob_noteNameText, mob_freqText )
            mob_keyboard.markKey ( tone + 12 )
            self.wait ( 1 )
            self.play (
                mob_keyboard.animate.resetMarks ( ),
                FadeOut ( mob_note, mob_noteNameText, mob_freqText ),
                run_time = 0.5,
            )
        
        def animateInterval ( startDegree: int, degreeDiff: int ):
            degrees = np.arange ( degreeDiff + 1 ) + startDegree
            mob_scale = mob_staff.createScale (
                degrees - 6,
                noteheadType = it.chain ( 
                    ( "whole", ), 
                    it.repeat ( "black", degreeDiff - 1 ), 
                    ( "whole", ) 
                ),
                buff = 1.5,
                add = False,
            ).shiftHpos ( 10 )
            
            startTone = scaleDegree2Tone ( startDegree )
            endTone = scaleDegree2Tone ( startDegree + degreeDiff )
            
            for i, mob_note in enumerate ( mob_scale ):
                degree = startDegree + i
                tone = scaleDegree2Tone ( degree )
                self.add ( mob_note )
                mob_keyboard.resetMarks ( )\
                    .markKey ( tone + 12 )\
                    .markKey ( startTone + 12, markColor = MARK_GREEN )
                self.wait ( 0.25 )
                
            mob_firstNote = mob_scale [ 0 ]
            mob_lastNote = mob_scale [ -1 ]
            arrowStartPoint = mob_firstNote.mob_noteheads.get_center ( )
            arrowEndPoint = mob_lastNote.mob_noteheads.get_center ( )
            mob_arrow = ArcBetweenPoints ( 
                arrowStartPoint, arrowEndPoint, - PI / 2,
                color = RED,
            ).add_tip ( **tipConfig ).shift ( UP * 0.25 )
            mob_intervalText = Text (
                getIntervalAbbr ( startDegree, degreeDiff ),
                **newTextConfig ( fs = 1.5 ),
            ).move_to ( noteNameTextPosition )
            mob_intervalNameText = Text (
                getIntervalName ( startDegree, degreeDiff ),
                **newTextConfig ( fs = 1.5 ),
            ).move_to ( freqTextPosition )
            
            self.play ( 
                Create ( mob_arrow ), 
                FadeIn ( mob_intervalText, mob_intervalNameText ),
                run_time = 0.5 
            )
            self.wait ( 0.5 )
            self.play (
                FadeOut ( mob_scale [ 1 : -1 ], mob_arrow ),
                mob_scale [ 0 ].animate.setHpos ( 14 ),
                mob_scale [ -1 ].animate.setHpos ( 22 ),
                mob_keyboard.animate\
                    .resetMarks ( )\
                    .markKey ( startTone + 12, markColor = MARK_GREEN )\
                    .markKey ( endTone + 12, markColor = MARK_GREEN ),
                run_time = 0.5,
            )
            self.wait ( 2 )
            self.play (
                FadeOut (
                    mob_scale [ 0 ], mob_scale [ -1 ],
                    mob_intervalText, mob_intervalNameText,
                ),
                mob_keyboard.animate.resetMarks ( ),
                run_time = 0.5,
            )
        
        animatePitch ( 0 )
        animatePitch ( 9 )
        # np.random.seed ( 0 )
        # randomTones = np.arange ( 24 )
        # print ( randomTones )
        # for randomTone in randomTones:
        #     animatePitch ( randomTone )
            
        self.next_section ( )
        
        animateInterval ( 0, 7 ) # 纯八度
        animateInterval ( 1, 7 ) # 纯八度
        
        # 展示八度的频率比为 2
        
        mob_longStaff = Staff ( **staffConfig, staffLength = 70 )\
            .center ( ).next_to ( mob_keyboard, DOWN, buff = 1.5 )
        mob_longStaff.createClef ( "F" ).setHpos ( 2 )
        mob_longStaff.createClef ( "G", change = True ).setHpos ( 22 )
        mob_octaves = mob_longStaff.createScale ( 
            ( -1, -6, 1, 8 ),
            noteheadType = "whole",
            buff = it.chain ( ( 20, ), it.repeat ( 12 ) ),
            add = False,
        ).shiftHpos ( 12 )
        
        mob_freqNote = Text ( 
            "频率 (Hz)", **textConfig, 
            color = YELLOW 
        )   .align_to ( mob_longStaff.mob_staffLines, LEFT )\
            .next_to ( mob_longStaff.mob_staffLines, UP, buff = 0.25, coor_mask = UP )
        
        mob_temp = mob_staff.copy ( )
        self.remove ( mob_staff )
        self.add ( mob_temp )
        self.play ( 
            FadeIn ( mob_freqNote ),
            Transform ( mob_temp, mob_longStaff ), 
            run_time = 1,
        )
        self.remove ( mob_temp )
        self.add ( mob_longStaff )
        
        mob_lastNote = None
        mob_lastFreqText = None
        mob_freqTexts = VGroup ( )
        
        for i, mob_note in enumerate ( mob_octaves ):
            mob_freqText = Text ( 
                f"{pitch2Freq ( 12 * ( i + 4 ) ):.2f}", 
                **textConfig,
                color = YELLOW,
            )   .move_to ( mob_note.mob_noteheads )\
                .next_to ( 
                    mob_longStaff.mob_staffLines, DOWN, 
                    buff = 0.4, coor_mask = UP,
                )
            mob_freqTexts.add ( mob_freqText )
            
            if mob_lastNote is None:
                self.play (
                    FadeIn ( mob_freqText, mob_note ),
                    mob_keyboard.animate\
                        .markKey ( i * 12, markColor = MARK_GREEN ),
                    run_time = 0.5,
                )
                self.wait ( 1 )
            else:
                mob_tempNote = mob_lastNote.copy ( )
                mob_tempFreqText = mob_lastFreqText.copy ( )
                mob_tempFreqText.save_state ( )
                mob_tempFreqText.move_to ( mob_freqText )
                mob_mul2Text = MathTex ( 
                    r"\times 2", color = RED, 
                    **latexConfig 
                ).next_to ( mob_tempFreqText, RIGHT, 0.2 )
                mob_tempFreqText.restore ( )
                
                arrowStartPoint = mob_lastNote.mob_noteheads.get_center ( )
                arrowEndPoint = mob_note.mob_noteheads.get_center ( )
                mob_arrow = ArcBetweenPoints (
                    arrowStartPoint, arrowEndPoint, -PI / 2,
                    color = RED,
                ).add_tip ( **tipConfig ).shift ( UP * 0.25 )
                
                self.add ( mob_tempNote, mob_tempFreqText )
                self.play (
                    Transform ( mob_tempNote, mob_note, run_time = 1 ),
                    mob_tempFreqText.animate ( run_time = 1 )\
                        .move_to ( mob_freqText ),
                    Succession (
                        Wait ( 0.5 ),
                        AnimationGroup (
                            FadeIn ( mob_mul2Text ),
                            Create ( mob_arrow ),
                            mob_keyboard.animate\
                                .markKey ( i * 12, markColor = MARK_GREEN ),
                            run_time = 0.5
                        )
                    )
                )
                self.play (
                    Transform ( mob_tempFreqText, mob_freqText ),
                    FadeOut ( mob_mul2Text ),
                    run_time = 0.5
                )
                mob_arrow.reverse_points ( )
                self.play (
                    Uncreate ( mob_arrow ),
                    run_time = 0.5,
                )
                self.remove ( mob_tempNote, mob_tempFreqText )
                self.add ( mob_note, mob_freqText )
            
            mob_lastNote = mob_note
            mob_lastFreqText = mob_freqText
        
        self.wait ( 2 )
        
        mob_temp = mob_longStaff.copy ( )
        self.remove ( mob_longStaff )
        self.add ( mob_temp )
        self.play ( 
            Transform ( 
                mob_temp, mob_staff, 
                run_time = 1 
            ), 
            FadeOut ( 
                mob_octaves, mob_freqNote, *mob_freqTexts,
                run_time = 0.5,
            ),
            mob_keyboard.animate.resetMarks ( ),
        )
        self.remove ( mob_temp )
        self.add ( mob_staff )
        
        animateInterval ( 0, 4 ) # 纯五度
        animateInterval ( 0, 2 ) # 大三度
        animateInterval ( 0, 5 ) # 大六度
        self.wait ( 2 )

class FrequencyExponentialScene ( Scene ):
    def construct ( self ):
        w, h = 10, 5
        xbuff, ybuff = 3, 25
        nOctaves = 3
        xStart = 60
        xEnd = xStart + nOctaves * 12
        xFocusEnd = xStart + 12
        xmin, xmax = xStart - xbuff, xEnd + xbuff
        xFocusMax = xFocusEnd + xbuff
        ymin, ymax = 0, pitch2Freq ( xmax ) + ybuff
        yFocusMax = pitch2Freq ( xFocusMax ) + ybuff
        boxCenter = np.array (( 0.25, 0.15, 0 ))
        
        mob_box = Rectangle ( height = 5, width = 10 )\
            .set_stroke ( width = 2 )\
            .move_to ( boxCenter )
        mob_axes = Axes ( 
            x_length = w, y_length = h,
            x_range = ( xmin, xmax ),
            y_range = ( ymin, ymax ),
        )
        mob_axes.shift ( 
            Rectangle.get_critical_point ( mob_box, DL ) -
            mob_axes.coords_to_point ( xmin, ymin )
        )
        mob_graph = mob_axes.plot ( pitch2Freq, color = RED )\
            .set_z_index ( 1 )
        mob_pitchText = Text ( "音高 (半音)", **textConfig )\
            .align_to ( mob_box, DR ).shift ( 0.25 * UL )\
            .add_background_rectangle ( )\
            .set_z_index ( 2 )
        mob_freqText = Text ( "频率 (Hz)", **textConfig )\
            .align_to ( mob_box, UL ).shift ( 0.25 * DR )\
            .add_background_rectangle ( )\
            .set_z_index ( 2 )
        mob_pitchNoteText = Tex ( 
            "注：此处 $x$ 轴的 60 表示钢琴键盘上中央 C 的位置",
            **latexConfig,
        ).to_corner ( UL, 0.25 )
        
        self.play ( FadeIn ( mob_box, mob_pitchText, mob_freqText, run_time = 1 ) )
        self.play ( Create ( mob_graph, run_time = 1 ) )
        
        var_pitch = ValueTracker ( 60 )
        mob_lineToX = Line ( stroke_width = 2 ).set_stroke ( opacity = 0.5 )
        mob_lineToY = Line ( stroke_width = 2 ).set_stroke ( opacity = 0.5 )
        mob_pointOnCurve = Dot ( radius = 0.06 ).set_z_index ( 2 )
        mob_freqValue = DecimalNumber ( 0, font_size = latexFs ( 1 ) )
        mob_pitchValue = Integer ( 0, font_size = latexFs ( 1 ) )
        
        def _update ( mob: Mobject | None = None ):
            x = var_pitch.get_value ( )
            y = pitch2Freq ( x )
            pointOnCurve = mob_axes.coords_to_point ( x, y )
            pointOnX = mob_axes.coords_to_point ( x, ymin )
            pointOnY = mob_axes.coords_to_point ( xmin, y )
            mob_lineToX.put_start_and_end_on ( pointOnX, pointOnCurve )
            mob_lineToY.put_start_and_end_on ( pointOnY, pointOnCurve )
            mob_pointOnCurve.move_to ( pointOnCurve )
            mob_freqValue.set_value ( y ).next_to ( pointOnY, LEFT, 0.25 )
            mob_pitchValue.set_value ( x ).next_to ( pointOnX, DOWN, 0.25 )
            
        mob_lineToX.add_updater ( _update )
        _update ( ) 
        self.play ( 
            FadeIn ( 
                mob_lineToX, mob_lineToY, mob_pointOnCurve,
                mob_pitchValue, mob_freqValue, 
                mob_pitchNoteText,
                run_time = 0.5 
            ) 
        )
        self.wait ( 0.5 )
        self.play (
            var_pitch.animate.set_value ( xEnd ),
            run_time = 5,
            rate_func = rf.ease_in_out_quad,
        )
        self.wait ( 0.5 )
        self.play (
            var_pitch.animate.set_value ( xStart ),
            run_time = 5,
            rate_func = rf.ease_in_out_quad,
        )
        self.wait ( 2 )
        mob_lineToX.clear_updaters ( )
        
        def createIndication ( i, showFreq: bool = False ):
            x = 60 + i
            y = pitch2Freq ( x )
            pointOnCurve = mob_axes.coords_to_point ( x, y )
            pointOnX = mob_axes.coords_to_point ( x, ymin )
            pointOnY = mob_axes.coords_to_point ( xmin, y )
            mob_lineToX = Line ( pointOnX, pointOnCurve, stroke_width = 2 )\
                .set_stroke ( opacity = 0.5 )
            mob_lineToY = Line ( pointOnY, pointOnCurve, stroke_width = 2 )\
                .set_stroke ( opacity = 0.5 )
            mob_pointOnCurve = Dot ( pointOnCurve, radius = 0.06 )\
                .set_z_index ( 2 )
            mob_pitchValue = Text ( f"{x}", **newTextConfig ( fs = 1 ) )\
                .next_to ( pointOnX, DOWN, 0.25 )
            mob_indication =  VGroup ( 
                mob_lineToX, mob_lineToY, 
                mob_pointOnCurve, mob_pitchValue, 
            )
            if showFreq:
                mob_freqValue = Text ( f"{y:.2f}", **newTextConfig ( fs = 1 ) )\
                    .next_to ( pointOnY, LEFT, 0.25 )
                mob_indication.add ( mob_freqValue )
            return mob_indication
            
        mob_indications = VGroup ( )
        def _getAnimations ( ):
            for i in range ( 1, 4 ):
                mob_indication = createIndication ( i * 12, showFreq = True )
                mob_indications.add ( mob_indication )
                yield FadeIn ( mob_indication, run_time = 0.5 )
        
        self.play ( LaggedStart ( *_getAnimations ( ), lag_ratio = 0.5 ) )
        self.wait ( 1 )
        
        mob_focusBox = rectByCorners (
            mob_axes.c2p ( xmin, ymin ),
            mob_axes.c2p ( xFocusMax, yFocusMax ),
        )   .set_fill ( color = WHITE, opacity = 0.25 )\
            .set_stroke ( width = 0, opacity = 0 )
        
        var_t = ValueTracker ( 0 )
        
        def updateGraph ( mob ):
            nonlocal mob_axes
            t = var_t.get_value ( )
            newXMax = xmax - ( xmax - xFocusMax ) * t
            newYMax = ymax - ( ymax - yFocusMax ) * t
            mob_axes = Axes (
                x_length = w, y_length = h,
                x_range = ( xmin, newXMax ),
                y_range = ( ymin, newYMax ),
            )
            mob_axes.shift ( 
                Rectangle.get_critical_point ( mob_box, DL ) -
                mob_axes.coords_to_point ( xmin, ymin )
            )
            mob.become (  
                mob_axes.plot ( pitch2Freq, color = RED )\
                    .set_z_index ( 1 )
            )
            
        def updateFocusBox ( mob ):
            newEndpoint = mob_axes.c2p ( xFocusMax, yFocusMax )
            reshapeToCorners ( 
                mob, 
                mob_box.get_critical_point ( DL ),
                newEndpoint 
            )
        
        self.play (
            FadeIn ( mob_focusBox, run_time = 0.5 ),
        )
        mob_graph.add_updater ( updateGraph )
        mob_focusBox.add_updater ( updateFocusBox )
        self.play (
            FadeOut (
                mob_lineToX, mob_lineToY, 
                mob_pointOnCurve,
                mob_pitchValue, mob_freqValue,
                mob_indications,
                run_time = 0.5
            ),
            var_t.animate ( run_time = 1 ).set_value ( 1 ),
        )
        mob_graph.clear_updaters ( )
        mob_focusBox.clear_updaters ( )
        self.play ( FadeOut ( mob_focusBox, run_time = 0.25 ) )
        
        mob_indications = VGroup ( )
        def _getAnimations ( ):
            for i in range ( 13 ):
                mob_indication = createIndication ( i, showFreq = i % 12 == 0 )
                mob_indications.add ( mob_indication )
                yield FadeIn ( mob_indication, run_time = 0.5 )
        self.play ( LaggedStart ( *_getAnimations ( ), lag_ratio = 0.5 ) )
        self.wait ( 2 ) 

class FrequencyRatioScene ( Scene ):
    def construct ( self ):
        clefType = "G"
        staffLength = 70
        newKeyAcciCount = -1
        newKeyTonic = newKeyAcciCount * 7 % 12
        newKeyStartDegree = newKeyAcciCount * 4 % 7
        alteredDegrees = _getAlteredDegrees ( newKeyAcciCount )
        
        noteDegrees = np.array ((
            0, 2, 4, -1, 0, 1, 0,
            5, 4, 7, 4, 3, 2, 3, 2,
        ))
        noteDurations = np.array ((
            2, 1, 1, 1.5, 0.25, 0.25, 2,
            2, 1, 1, 1, 0.5, 0.25, 0.25, 1,
        ))
        summedNoteDurations = np.empty ( len ( noteDurations ) )
        summedNoteDurations [ 0 ] = 0
        summedNoteDurations [ 1: ] = np.cumsum ( noteDurations [ :-1 ] )
        bpm = 144
        q, r = np.divmod ( noteDegrees, 7 )
        melody = q * 12 + _majorScale [ r ]
        
        melodyAccidentals = ( 
            ( -1 if newKeyAcciCount < 0 else 1 ) 
            if i in alteredDegrees else None 
            for i in noteDegrees 
        )
        scaleAccidentals = ( 
            ( -1 if newKeyAcciCount < 0 else 1 ) 
            if i in alteredDegrees else None 
            for i in range ( 7 ) 
        )
        
        freqs1Center = np.array (( 0, 1.35, 0 ))
        freqs2Center = np.array (( 0, -1.35, 0 ))
        staff1Center = np.array (( 0, 1.75, 0 ))
        staff2Center = np.array (( 0, -1.25, 0 ))
        
        # 第一部分：频率展示
        
        mob_textTitle = Tex ( "音程关系 $\\rightarrow$ 频率比", **newLatexConfig ( fs = 1.25 ) )\
            .to_corner ( UL, buff = 0.25 )
        mob_frequencyNote = Text ( 
            "频率 (单位 Hz)", color = YELLOW, 
            **textConfig 
        ).to_corner ( UR, buff = 0.25 )
        
        def createFreqs ( freqs ):
            mob_noteBlocks = Group ( 
                *(
                    NoteBlock ( size = 0.75 )
                    for _ in range ( len ( freqs ) )
                ),
            )
            mob_freqTexts = VGroup (
                *(
                    Text ( 
                        f"{freq: 4.2f}", 
                        **newTextConfig ( fs = 1.25 ) 
                    ) 
                    for freq in freqs
                ),  
            )
            Group ( *mob_noteBlocks, *mob_freqTexts )\
                .arrange_in_grid ( rows = 2, buff = 0.25 )
            return Group ( mob_noteBlocks, mob_freqTexts )
        
        self.play ( FadeIn ( mob_textTitle, run_time = 0.5 ) )
        freqs = pitch2Freq ( melody [ :7 ] + 72 )
        mob_freqs1 = createFreqs ( freqs )
        
        self.play ( 
            FadeIn ( mob_freqs1 [ 0 ], run_time = 0.5 ), 
            Write ( mob_freqs1 [ 1 ], run_time = 1 ),
        )
        
        def getMelodyAnimations ( mob_freqs, tonic: int = 0 ):
            for mob_noteBlock, mob_text, startDur, tone in \
                    zip ( *mob_freqs, summedNoteDurations, melody ):
                delay = startDur * 60 / bpm
                addMidi ( 
                    self, generateNoteMidi ( tone + 72 + tonic ), 
                    timeOffset = delay 
                )
                yield Succession (
                    Wait ( delay ),
                    AnimationGroup (
                        Indicate ( mob_text, run_time = 0.5 ),
                        mob_noteBlock.animatePlay ( ),
                    ),
                )
        
        self.play ( *getMelodyAnimations ( mob_freqs1 ) )
        self.play ( mob_freqs1.animate.move_to ( freqs1Center ), run_time = 1 )
        
        newFreqs = pitch2Freq ( melody [ :7 ] + 72 + newKeyTonic )
        mob_freqs2 = createFreqs ( newFreqs )\
            .move_to ( freqs2Center )
            
        mob_temp = mob_freqs1.copy ( )
        self.play ( mob_temp.animate.move_to ( freqs2Center ), run_time = 1 )
        
        mob_multiplyTexts = VGroup ( )
        for mob_freqText in mob_temp [ 1 ]:
            mob_multiplyText = MathTex ( 
                fr"\times 2^{{{ Q ( newKeyTonic, 12 ) }}}",
                color = RED,
                **newLatexConfig ( fs = 1.25 )
            ).next_to ( mob_freqText, DOWN, buff = 0.25 )
            mob_multiplyTexts.add ( mob_multiplyText )
        self.play ( FadeIn ( mob_multiplyTexts, run_time = 0.5 ) )
        self.wait ( 0.5 )
        self.play ( 
            Transform ( mob_temp [ 1 ], mob_freqs2 [ 1 ], run_time = 1 ),
            FadeOut ( mob_multiplyTexts ),
        )
        self.remove ( mob_temp )
        self.add ( mob_freqs2 )
        self.wait ( 1 )
        self.play ( *getMelodyAnimations ( mob_freqs2, newKeyTonic ) )
        self.wait ( 2 )
        self.play ( 
            FadeOut ( 
                mob_freqs1, mob_freqs2, 
                run_time = 0.5 
            ) 
        )
        
        # 第二部分：谱表展示
        
        # 上方谱表，展示 C 大调的旋律
        mob_staff1 = Staff ( **staffConfig, staffLength = staffLength )\
            .move_to ( staff1Center )
        mob_clef1 = mob_staff1.createClef ( clefType ).setHpos ( 2 )
        mob_melody1 = mob_staff1.createScale ( 
            vpos = noteDegrees + 1, 
            buff = 3, accidentalSpaceRatio = 0,
        ).after ( mob_clef1, 3 )
        
        # 下方谱表，展示 F 大调的旋律
        mob_staff2 = Staff ( **staffConfig, staffLength = staffLength )\
            .move_to ( staff2Center )
        mob_clef2 = mob_staff2.createClef ( clefType ).setHpos ( 2 )
        mob_melody2 = mob_staff2.createScale ( 
            vpos = noteDegrees + 4, 
            accidentals = melodyAccidentals,
            buff = 3, accidentalSpaceRatio = 0,
        ).after ( mob_clef2, 3 )
        
        # 出示谱表 1
        self.play ( Create ( mob_staff1, run_time = 1 ) )
        
        # 谱表 1 下移得到谱表 2
        mob_temp = mob_staff1.copy ( )
        self.play ( Transform ( mob_temp, mob_staff2, run_time = 1 ) )
        self.remove ( mob_temp )
        self.add ( mob_staff2 )
        self.play ( FadeIn ( mob_frequencyNote, run_time = 0.5 ) )
        
        # 谱表 1 上音符的频率
        mob_freqTexts1 = VGroup ( )
        for mob_note, tone in zip ( mob_melody1, melody ):
            freq = pitch2Freq ( tone + 72 )
            mob_freqText = Text ( f"{freq:.2f}", color = YELLOW, **textConfig )\
                .rotate ( -PI / 4 )\
                .align_to ( mob_note.mob_noteheads, LEFT )\
                .next_to ( mob_note.parent.mob_staffLines, DOWN, 0.3, coor_mask = UP )
            self.add ( mob_freqText )
            mob_freqTexts1.add ( mob_freqText )
            self.wait ( 0.05 )
        
        # 谱表 2 上音符的频率
        mob_freqTexts2 = VGroup ( )
        def _getAnimations ( ):
            for mob_note, tone, mob_oldFreqText in zip ( mob_melody2, melody, mob_freqTexts1 ):
                freq = pitch2Freq ( tone + 72 + newKeyTonic )
                mob_freqText = mob_oldFreqText.copy ( )
                mob_transformResult = Text ( f"{freq:.2f}", color = YELLOW, **textConfig )\
                    .rotate ( -PI / 4 )\
                    .align_to ( mob_note.mob_noteheads, LEFT )\
                    .next_to ( mob_note.parent.mob_staffLines, DOWN, 0.3, coor_mask = UP )
                mob_freqTexts2.add ( mob_freqText )
                yield Transform ( mob_freqText, mob_transformResult )
        
        # 显示频率之间的比例关系
        mob_arrow = Line ( 
            mob_clef1.get_critical_point ( DOWN ) + DOWN * 0.25,
            mob_clef2.get_critical_point ( UP ) + UP * 0.25,
            color = RED, 
        ).add_tip ( **tipConfig )
        mob_freqRatioText = MathTex (
            rf"\times 2^{{{ frac2Latex ( Q ( newKeyTonic, 12 ), slant = True ) }}}",
            color = RED,
            **newLatexConfig ( fs = 1.25 )
        )   .next_to ( mob_arrow, RIGHT, buff = 0.25 )\
            .shift ( DOWN * 0.25 )
            
        self.play ( 
            Create ( mob_arrow, run_time = 1 ),
            FadeIn ( mob_freqRatioText, run_time = 0.5 ),
            LaggedStart ( 
                *_getAnimations ( ), 
                lag_ratio = 0.25, run_time = 4, 
            ), 
        )
        
        mob_staff1.remove ( mob_melody1 )
        mob_staff2.remove ( mob_melody2 )
        self.add ( mob_melody1, mob_melody2 )
        
        mob_scale1 = mob_staff1.createScale (
            vpos = np.arange ( 7 ) + 1,
            buff = 7, accidentalSpaceRatio = 0,
            add = False,
        ).shiftHpos ( 15 )
        mob_scale2 = mob_staff2.createScale (
            vpos = np.arange ( 7 ) + 1 + newKeyStartDegree,
            accidentals = scaleAccidentals,
            buff = 7, accidentalSpaceRatio = 0,
            add = False,
        ).shiftHpos ( 15 )
        
        def getScaleFreqTexts ( mob_scale: Scale, startTone: int = 0 ):
            mob_scaleFreqTexts = VGroup ( )
            for i, mob_note in enumerate ( mob_scale ):
                mob_freqText = Text ( 
                    f"{pitch2Freq ( 72 + _majorScale [ i ] + startTone ):.2f}",
                    color = YELLOW, **textConfig,
                )   .move_to ( mob_note.get_center ( ) )\
                    .next_to ( mob_note.parent.mob_staffLines, DOWN, 0.3 )
                mob_scaleFreqTexts.add ( mob_freqText )
            return mob_scaleFreqTexts
        
        mob_scaleFreqTexts1 = getScaleFreqTexts ( mob_scale1 )
        mob_scaleFreqTexts2 = getScaleFreqTexts ( mob_scale2, newKeyTonic )
        
        self.wait ( 1 )
        self.play (
            Transform ( mob_melody1, mob_scale1 ),
            Transform ( mob_melody2, mob_scale2 ),
            Transform ( mob_freqTexts1, mob_scaleFreqTexts1 ),
            Transform ( mob_freqTexts2, mob_scaleFreqTexts2 ),
            run_time = 1,
        )
        self.wait ( 1 )
        self.play (  
            FadeOut ( mob_arrow, mob_freqRatioText, run_time = 0.5 ),
        )
        
        mob_keyNameText1 = _createKeyNameText ( 0, fs = 1.25 )\
            .next_to ( mob_staff1, DOWN, buff = 0.25 )\
            .align_to ( mob_staff1, LEFT )
        mob_keyNameText2 = _createKeyNameText ( newKeyAcciCount, fs = 1.25 )\
            .next_to ( mob_staff2, DOWN, buff = 0.25 )\
            .align_to ( mob_staff2, LEFT )
            
        self.play (
            FadeIn ( 
                mob_keyNameText1, mob_keyNameText2,
                run_time = 0.5,
            ),
        )

        self.wait ( 2 )

class SineWaveScene ( Scene ):
    def construct ( self ):
        unitWavelength = 1
        unitAmplitude = 0.6
        
        def getSineFunction ( freq: float, amp: float = 1 ):
            return ( 
                lambda x: amp * unitAmplitude * 
                np.sin ( 2 * PI * freq * x / unitWavelength )
            )
        def combineFunctions ( 
                operator: Callable [ ..., float ], 
                *funcs: Callable [ [ float ], float ] 
        ) -> Callable [ [ float ], float ]:
            def _fn ( x: float ):
                return operator ( *( fn ( x ) for fn in funcs ) )
            return _fn
        
        rationalFreqs = ( Q ( 1 ), Q ( 5, 4 ), Q ( 3, 2 ) )
        frequencies = np.array ( tuple ( map ( float, rationalFreqs ) ) )
        denoms = np.array ( tuple ( fr.denominator for fr in rationalFreqs ) )
        lcmDenoms = np.lcm.reduce ( denoms )
        
        bottomGap = 0.75
        rx = config.frame_x_radius
        ry = config.frame_y_radius
        n = len ( frequencies ) + 1
        totalHeight = 2 * ry - bottomGap
        regionHeight = totalHeight / n
        fillRate = 0.6
        amp = regionHeight * fillRate / 2
        colors = ( RED, GREEN, BLUE )
        funcs = [ ]
        
        def createVline ( nPeriods: float ) -> Line:
            x = -rx + nPeriods * unitWavelength
            return Line (
                ( x, -ry + bottomGap, 0 ), ( x, ry, 0 ),
                stroke_width = 1,
                stroke_opacity = 0.25
            )
        
        mob_hlines = VGroup ( )
        mob_vlines = VGroup ( )
        for i in range ( n ):
            y = -ry + bottomGap + i * regionHeight
            mob_line = Line (
                ( -rx, y, 0 ), ( rx, y, 0 ),
                stroke_width = 2,
                stroke_opacity = 0.5,
            )
            mob_hlines.add ( mob_line )
        for i in range ( int ( 2 * rx // unitWavelength ) + 1 ):
            mob_vlines.add ( createVline ( i ) )
        
        
        def getSineFunction ( freq ):
            return lambda x: np.sin ( TAU * x * freq )
        
        mob_graphs = VGroup ( )
        mob_freqTexts = VGroup ( )
        for i, ( freq, freqFrac ) in enumerate ( zip ( frequencies, rationalFreqs ) ):
            y = -ry + bottomGap + ( i + 1.5 ) * regionHeight
            ratioNumber = freqFrac.numerator * lcmDenoms // freqFrac.denominator
            color = loop ( colors, i )
            func = getSineFunction ( freq )
            plotFunc = lambda x: func ( x / unitWavelength ) * amp
            funcs.append ( func )
            mob_graph = FunctionGraph ( 
                plotFunc, x_range = ( 0, 4 * rx ), 
                color = color 
            ).shift ( ( -rx, y, 0 ) ).set_z_index ( 1 )
            mob_graph.save_state ( )
            mob_temp = FunctionGraph ( 
                plotFunc, x_range = ( 0, 2 * rx ), 
                color = color 
            ).shift ( ( -rx, y, 0 ) ).set_z_index ( 1 )
            mob_graph.become ( mob_temp )
            
            mob_freqText = Text ( str ( ratioNumber ), **newTextConfig ( fs = 2.5 ) )\
                .shift ( UP * y ).to_edge ( RIGHT, buff = 0.5 )\
                .add_background_rectangle ( buff = 0.2 )\
                .set_z_index ( 2 )
            mob_graphs.add ( mob_graph )
            mob_freqTexts.add ( mob_freqText )
        
        def getMixedGraph ( n, storeState = False ):
            y = -ry + bottomGap + regionHeight / 2
            # if n == 0:
            #     return Line ( ( -rx, y, 0 ), ( rx, y, 0 ), color = PINK )
            if n == 0:
                plotFunc = lambda _: 0
            else:
                mixedFunc = combineFunctions ( asVarArg ( np.average ), *funcs [ :n ] )
                plotFunc = lambda x: mixedFunc ( x / unitWavelength ) * amp
            
            mob_temp = FunctionGraph ( 
                plotFunc, color = PINK,
                x_range = ( 0, 2 * rx ),
            ).shift ( ( -rx, y, 0 ) ).set_z_index ( 1 )
            
            if storeState:
                fullMixedFunc = combineFunctions ( asVarArg ( np.average ), *funcs [ :n ] )
                fullPlotFunc = lambda x: fullMixedFunc ( x / unitWavelength ) * amp
                mob_graph = FunctionGraph ( 
                    fullPlotFunc, color = PINK,
                    x_range = ( 0, 4 * rx ),
                ).shift ( ( -rx, y, 0 ) ).set_z_index ( 1 )
                mob_graph.save_state ( )
                mob_graph.become ( mob_temp )
            else:
                mob_graph = mob_temp
            
            return mob_graph
        
        mob_mixedGraph = getMixedGraph ( 0, storeState = True )
        mob_mixedGraphBg = Rectangle (
            width = 2 * rx, height = regionHeight,
            fill_opacity = 0.05,
            stroke_width = 0,
        ).shift ( UP * ( -ry + bottomGap + regionHeight / 2 ) )\
            .set_z_index ( -1 )
        self.play ( 
            FadeIn ( mob_hlines, mob_vlines, mob_mixedGraphBg, run_time = 0.5 ),
            Create ( mob_mixedGraph ), 
            run_time = 0.5 
        )
        
        for i, ( mob_graph, mob_freqText ) in \
                enumerate ( zip ( mob_graphs, mob_freqTexts ) ):
            self.play (  
                Create ( mob_graph ),
                FadeIn ( mob_freqText ),
                mob_mixedGraph.animate.become ( getMixedGraph ( i + 1 ) ),
                run_time = 1, 
            )
            mob_graph.restore ( )
            mob_graph.save_state ( )
            self.wait ( 0.5 )
        
        periodWidth = lcmDenoms * unitWavelength
        mob_periodRect = Rectangle (
            color = WHITE, height = totalHeight,
            width = periodWidth,
            fill_opacity = 0.15,
            stroke_width = 0,
        )   .shift ( ( periodWidth / 2 - rx,  bottomGap / 2, 0 ) )\
            .set_z_index ( -1 )\
            .reverse_points ( )
        mob_periodRect.save_state ( )
        mob_periodRect.stretch_to_fit_width ( 0 )\
            .set_x ( -rx )
        mob_periodVline = createVline ( 0 )\
            .set_stroke ( width = 2, opacity = 1 )
        self.add ( mob_periodVline, mob_periodRect )
        self.play ( 
            mob_periodRect.animate.restore ( ), 
            mob_periodVline.animate.shift ( RIGHT * periodWidth ),
            run_time = 1,
        )
        self.wait ( 2 )
        
class MajorScaleScene ( Scene ):
    def construct ( self ):
        numberLinePosition = np.array (( 0, 2, 0 ))
        keyboardPosition = np.array (( -3.25, -0.75, 0 ))
        staffPosition = np.array (( 3.3, -0.15, 0 ))  
        noteTextPosition = np.array (( 3.3, -1.5, 0 ))
        numberLineBuff = 0.5
        clefType = "G"

        majorScaleDiffs = np.diff ( np.append ( _majorScale, 12 ) )
        
        mob_numberLine = NumberLine ( 
            x_range = ( -numberLineBuff, 12 + numberLineBuff ),
            length = 12,
        ).shift ( numberLinePosition )
        mob_keyboard = MultiOctavePianoKeyboard (
            octaves = 2,
            **keyboardConfig,
        ).move_to ( keyboardPosition )
        mob_staff = Staff ( **staffConfig, staffLength = 35 )\
            .move_to ( staffPosition )
        mob_clef = mob_staff.createClef ( clefType ).setHpos ( 2 )
        self.play (  
            Create ( mob_numberLine ),
            FadeIn ( mob_keyboard, mob_staff ),
            run_time = 1,
        )
        self.wait ( 1 ),
        
        def createScaleDegreeText ( 
                i: int, fs: float = 1.25,
                hasStroke: bool = False,
        ) -> MathTex:
            mob = MathTex ( 
                rf"\hat{{{i + 1}}}", 
                **newLatexConfig ( fs = fs ),
            ).set_z_index ( 1 )
            
            if hasStroke:
                mob = withOutlineBackground ( mob )
                
            return mob
        
        def animateScaleGeneration ( acciCount: int ):
            mob_arrows = VGroup ( )
            mob_scaleDegrees = VGroup ( )
            mob_scaleDegreesOnKeys = VGroup ( )
            mob_intervalTexts = VGroup ( )
            mob_glowPoints = VGroup ( )
            
            tonic = acciCount * 7 % 12
            startDegree = acciCount * 4 % 7
            midiNote = tonic + 60
            
            alteredDegrees = _getAlteredDegrees ( acciCount )
            mob_majorNoteNameTexts = _createNoteNameTexts ( acciCount )\
                .move_to ( noteTextPosition )
            mob_keyNameText = _createKeyNameText ( 
                acciCount, 
                fs = 1.5, 
                showAcciCount = True 
            ).move_to ( noteTextPosition )
            mob_tonicText = mob_keyboard.alignToKey (
                tonic,
                Text ( "主\n音", **textConfig )\
                    .set_stroke ( 
                        width = 4, 
                        color = BLACK, 
                        background = True,
                        opacity = 0.75,
                    ),
            )
            mob_indicator = Circle ( radius = 0.1 )\
                .set_stroke ( width = 0 )\
                .set_fill ( color = RED, opacity = 1 )
                
            scaleNotePositions = np.arange ( 7 ) + ( startDegree - 6 )
            
            if acciCount == -7: 
                scaleNotePositions += 7
                
            mob_scale = mob_staff.createScale ( 
                vpos = scaleNotePositions,
                buff = 2,
                noteheadType = it.chain ( ( "whole", ), it.repeat ( "black" ) ),
                accidentals = ( 
                    None if i not in alteredDegrees else 
                    1 if acciCount > 0 else -1 
                    for i in range ( 7 ) 
                ),
                accidentalSpaceRatio = 0,
                add = False,
            ).after ( mob_clef, 4 )
                
            addMidi ( self, generateNoteMidi ( midiNote ), 0.1 )
            self.play (
                mob_keyboard.animate ( run_time = 0.25 )\
                    .markKey ( tonic, markColor = MARK_RED ),
                FadeIn ( mob_tonicText, run_time = 0.25 ),
                Flash ( mob_numberLine.n2p ( 0 ) ),
            )
            self.wait ( 0.5 )
            self.play ( FadeOut ( mob_tonicText, run_time = 0.25 ) )
            for i, ( tone, diff, mob_text, mob_note ) in \
                    enumerate ( zip ( 
                        _majorScale, 
                        majorScaleDiffs, 
                        mob_majorNoteNameTexts, 
                        mob_scale 
                    ) ):
                currentKey = tonic + _majorScale [ i ]
                midiNote = currentKey + 60
                p1 = mob_numberLine.n2p ( tone )
                p2 = mob_numberLine.n2p ( tone + diff )
                isSemitone = ( diff == 1 )
                
                mob_scaleDegree = createScaleDegreeText ( i )\
                    .next_to ( p1, DOWN )
                mob_glowPoint = addGlow ( Dot ( p1, radius = 0.06 ) )
                mob_scaleDegreeOnKey = mob_keyboard.alignToKey (
                    currentKey,
                    createScaleDegreeText ( i, 1, True ),
                )
                mob_arrow = ArcBetweenPoints ( 
                    p1, p2, angle = -PI / 2, 
                    color = BLUE if isSemitone else RED,
                ).add_tip ( **tipConfig )
                
                mob_intervalText = Text (
                    "半" if isSemitone else "全",
                    **newTextConfig ( fs = 1.25 ),
                ).next_to ( mob_arrow, UP, 0.2 )
                
                mob_arrows.add ( mob_arrow )
                mob_scaleDegrees.add ( mob_scaleDegree )
                mob_scaleDegreesOnKeys.add ( mob_scaleDegreeOnKey )
                mob_intervalTexts.add ( mob_intervalText )
                mob_glowPoints.add ( mob_glowPoint )
                
                addMidi ( self, generateNoteMidi ( midiNote ), 0.1 )
                
                if i in alteredDegrees:
                    mob_note.mob_noteheads.set_color (
                        RED if acciCount > 0 else GREEN 
                    )
                self.add (
                    mob_text,
                    mob_scaleDegree,
                    mob_scaleDegreeOnKey,
                    mob_note,
                )
                mob_keyboard.markKey ( currentKey )
                self.play ( FadeIn ( mob_glowPoint, run_time = 0.25 ) )
                
                var_t = ValueTracker ( 0 )
                
                def updateIndicator ( mob: Circle ):
                    t = int ( var_t.get_value ( ) )
                    if t >= diff: t = diff - 1
                    indicatorKey = currentKey + t + 1
                    mob_keyboard.alignToKey ( indicatorKey, mob )
                
                self.add ( mob_indicator )
                mob_indicator.add_updater ( updateIndicator )
                self.play (
                    var_t.animate ( run_time = 0.5 )\
                        .set_value ( diff ),
                    Create ( mob_arrow, run_time = 0.5 ),
                    FadeIn ( mob_intervalText, run_time = 0.25 ),
                )
                self.remove ( mob_indicator )
            
            # 高八度的主音 (但是乐谱上不显示)
            
            currentKey = 12 + tonic
            midiNote = currentKey + 60
            addMidi ( self, generateNoteMidi ( midiNote ), 0.1 )
            
            mob_scaleDegree = createScaleDegreeText ( 0 )\
                .next_to ( mob_numberLine.n2p ( 12 ), DOWN )
            mob_scaleDegreeOnKey = mob_keyboard.alignToKey (
                currentKey,
                createScaleDegreeText ( 0, 1, True ),
            )
            mob_glowPoint = addGlow ( Dot ( mob_numberLine.n2p ( 12 ), radius = 0.06 ) )
            mob_scaleDegrees.add ( mob_scaleDegree )
            mob_scaleDegreesOnKeys.add ( mob_scaleDegreeOnKey )
            mob_glowPoints.add ( mob_glowPoint )
            self.add (
                mob_scaleDegree,
                mob_scaleDegreeOnKey,
            )
            mob_keyboard.markKey ( currentKey )
            self.play ( FadeIn ( mob_glowPoint, run_time = 0.25 ) )
            self.wait ( 0.5 )
            
            # 显示调性名称
            
            self.play ( 
                Transform ( 
                    mob_majorNoteNameTexts, mob_keyNameText,
                    run_time = 0.5, 
                ),
                FadeOut ( mob_glowPoints, run_time = 0.25 ),
            )
            self.remove ( mob_majorNoteNameTexts )
            self.add ( mob_keyNameText )
            
            # 临时变音记号转调号
            
            lmob_copiedAccidentals = [ ]
            def _getAnimations ( ):
                for degree in alteredDegrees:
                    noteAccidental = mob_scale [ degree ].getAccidental ( )
                    lmob_copiedAccidentals.append ( noteAccidental.copy ( ) )
                    yield Indicate ( noteAccidental, scale_factor = 2, run_time = 0.5 )
            
            if acciCount != 0:
                self.play (
                    LaggedStart (
                        *_getAnimations ( ),
                        lag_ratio = 0.5,
                    ),
                )
            
            mob_keySig = mob_staff.createKeySig ( clefType, acciCount, add = False )\
                .after ( mob_clef, 1.5 )
            mob_newScale = mob_staff.createScale ( 
                vpos = scaleNotePositions,
                noteheadType = it.chain ( ( "whole", ), it.repeat ( "black" ) ),
                buff = 1.25,
                add = False,
            ).after ( mob_keySig, 2.5 )
            
            for i, mob_note in enumerate ( mob_newScale ):
                if i in alteredDegrees:
                    mob_note.mob_noteheads.set_color (
                        RED if acciCount > 0 else GREEN 
                    )
            
            def _getAnimations ( ):
                for mob_keySigAcci, mob_noteAcci in \
                        zip ( mob_keySig.accidentals ( ),  lmob_copiedAccidentals ):
                    yield mob_noteAcci.animate ( run_time = 0.5 )\
                        .move_to ( mob_keySigAcci )
                        
            mob_scale.become ( mob_scale.copyWithoutAcci ( ) )
            self.play ( 
                *_getAnimations ( ), 
                Transform ( mob_scale, mob_newScale, run_time = 1 ),
            )
            self.remove ( *lmob_copiedAccidentals, mob_scale )
            self.add ( mob_keySig, mob_newScale )
            
            if acciCount != 0:                
                self.play ( Circumscribe ( mob_keySig, time_width = 3 ) )
            
            self.wait ( 2 )
            
            self.play (
                FadeOut (
                    mob_scaleDegrees,
                    mob_arrows,
                    mob_scaleDegreesOnKeys,
                    mob_intervalTexts,
                    mob_newScale,
                    mob_keySig,
                    mob_keyNameText,
                    run_time = 0.5,
                ),
                mob_keyboard.animate ( run_time = 0.25 )\
                    .resetMarks ( ),
            )
        
        animateScaleGeneration ( 0 )
        animateScaleGeneration ( -1 )
        animateScaleGeneration ( 3 )
        # np.random.seed ( 1 )
        # acciCounts = np.concat ( ( np.arange ( -7, 0 ), np.arange ( 1, 8 ) ) ) 
        # np.random.shuffle ( acciCounts )
        # for acciCount in acciCounts:
        #     animateScaleGeneration ( acciCount )
        self.wait ( 2 )

class KeySignatureScene ( Scene ):
    def construct ( self ):
        clefType = "G"
        staffPosition = np.array (( -3.5, 3, 0 ))
        tablePosition = np.array (( 0, -0.5, 0 ))
        acciCountOrder = np.array ((
            0, 7, -5, 2, -3, 4, -1, 6, -6, 1, -4, 3, -2, 5, -7
        ))
        acciCountArgs = np.argsort ( acciCountOrder )
        
        mob_staff = Staff ( **staffConfig, staffLength = 35 )\
            .move_to ( staffPosition )
        mob_clef = mob_staff.createClef ( clefType ).setHpos ( 2 )
        self.add ( mob_staff )
        
        def createTableSide ( acciCounts, co5Order: bool = False ):
            mob_table = VGroup ( )
            for i in acciCounts:
                mob_table.add (
                    _createKeyNameText ( i, fs = 1 ),
                    *_createNoteNameTexts ( i, fs = 1, co5Order = co5Order ),
                )
            mob_table.arrange_in_grid ( 
                cols = 8, buff = ( 0.25, 0.25 ),
                col_alignments = "r" * 8,
                row_alignments = "u" * len ( acciCounts ),
                row_heights = ( 0.35, ) * len ( acciCounts ),
            )
            mob_table [ ::8 ].shift ( LEFT * 0.25 )
            return mob_table
        
        def createTable ( acciCounts, co5Order = False ):
            mob_tableLeft = createTableSide ( acciCounts [ :8 ], co5Order = co5Order )
            mob_tableRight = createTableSide ( acciCounts [ 8: ], co5Order = co5Order )
            VGroup ( mob_tableLeft, mob_tableRight )\
                .arrange_in_grid ( rows = 1, row_alignments = "u", buff = 1 )\
                .move_to ( tablePosition )
            mob_table = VGroup ( )
            itr = it.chain ( mob_tableLeft, mob_tableRight )
            while True:
                try:
                    mob_table.add ( next ( itr ) )
                    mob_table.add ( VGroup ( *it.islice ( itr, 7 ) ) )
                except StopIteration: break
            return mob_table

        mob_table = createTable ( acciCountOrder )
        mob_tableCo5Order1 = createTable ( acciCountOrder, co5Order = True )
        mob_tableCo5Order2 = createTable ( np.arange ( -7, 8 ), co5Order = True )
        
        def getKeyNameTextInTable ( acciCount: int ):
            tableOrder = acciCountArgs [ acciCount + 7 ]
            return mob_table [ tableOrder * 2 ]
        
        def getNoteNameTextsInTable ( acciCount: int ):
            tableOrder = acciCountArgs [ acciCount + 7 ]
            return mob_table [ tableOrder * 2 + 1 ]
        
        mob_keyNames = VGroup ( )
        mob_noteNameGroups = VGroup ( )
        
        def animateKeySignature ( acciCount: int ):
            startDegree = acciCount * 4 % 7
            alteredDegrees = _getAlteredDegrees ( acciCount )
            scaleNotePositions = np.arange ( 7 ) + ( startDegree - 6 )
            if acciCount == -7:  scaleNotePositions += 7
            
            mob_scale = mob_staff.createScale ( 
                vpos = scaleNotePositions,
                buff = 2,
                noteheadType = it.chain ( ( "whole", ), it.repeat ( "black" ) ),
                accidentals = ( 
                    None if i not in alteredDegrees else 
                    1 if acciCount > 0 else -1 
                    for i in range ( 7 ) 
                ),
                accidentalSpaceRatio = 0,
                add = False,
            ).after ( mob_clef, 4 )
            
            mob_keyNameText = _createKeyNameText ( acciCount )\
                .next_to ( mob_staff.mob_staffLines, RIGHT, 0.6 )
            mob_majorNoteNameTexts =_createNoteNameTexts ( acciCount, buff = 0.2 )\
                .next_to ( mob_keyNameText, RIGHT, 0.6 )
            mob_keyNames.add ( mob_keyNameText )
            mob_noteNameGroups.add ( mob_majorNoteNameTexts )
            
            self.add ( mob_keyNameText )
            self.wait ( 0.25 )
            for i, ( mob_noteNameText, mob_note ) in \
                    enumerate ( zip ( mob_majorNoteNameTexts, mob_scale ) ):
                if i in alteredDegrees:
                    mob_note.mob_noteheads.set_color (
                        RED if acciCount > 0 else GREEN 
                    )
                self.add ( mob_noteNameText, mob_note )
                self.wait ( 0.05 )
            
            lmob_copiedAccidentals = [ ]
            for degree in alteredDegrees:
                noteAccidental = mob_scale [ degree ].getAccidental ( )
                lmob_copiedAccidentals.append ( noteAccidental.copy ( ) )
            
            mob_keySig = mob_staff.createKeySig ( clefType, acciCount, add = False )\
                .after ( mob_clef, 1.5 )
            mob_newScale = mob_staff.createScale ( 
                vpos = scaleNotePositions,
                noteheadType = it.chain ( ( "whole", ), it.repeat ( "black" ) ),
                buff = 1.25,
                add = False,
            ).after ( mob_keySig, 2.5 )
            for i, mob_note in enumerate ( mob_newScale ):
                if i in alteredDegrees:
                    mob_note.mob_noteheads.set_color (
                        RED if acciCount > 0 else GREEN 
                    )
            
            def _getAnimations ( ):
                for mob_keySigAcci, mob_noteAcci in \
                        zip ( mob_keySig.accidentals ( ),  lmob_copiedAccidentals ):
                    yield mob_noteAcci.animate ( run_time = 0.5 )\
                        .move_to ( mob_keySigAcci )
            self.remove ( *mob_scale )
            mob_scale = mob_scale.copyWithoutAcci ( )
            
            self.play (
                Transform ( 
                    mob_keyNameText, 
                    getKeyNameTextInTable ( acciCount ) 
                ),
                Transform ( 
                    mob_majorNoteNameTexts, 
                    getNoteNameTextsInTable ( acciCount ) 
                ),
                *_getAnimations ( ),
                Transform ( mob_scale, mob_newScale ),
                run_time = 0.5,
            )
            
            self.wait ( 0.25 )
            self.remove ( mob_scale, *lmob_copiedAccidentals )
        
        for acciCount in acciCountOrder: animateKeySignature ( acciCount )
        
        def getReorderArgs ( acciCount: int ) -> np.ndarray:
            startDegree = acciCount * 4 % 7
            return np.roll ( _co5DegreeArgs, -startDegree )
        
        def _getAnimations ( ):
            for ( 
                    acciCount, mob_keyName1, 
                    mob_keyName2, mob_noteNames1, 
                    mob_noteNames2 
            ) in zip ( 
                    acciCountOrder, 
                    mob_keyNames, mob_tableCo5Order1 [ ::2 ], 
                    mob_noteNameGroups, mob_tableCo5Order1 [ 1::2 ] 
            ):
                reorderArgs = getReorderArgs ( acciCount )
                yield Transform ( mob_keyName1, mob_keyName2 )
                for reorderArg, mob_noteName in zip ( reorderArgs, mob_noteNames1 ):
                    yield Transform ( mob_noteName, mob_noteNames2 [ reorderArg ] )
        
        self.wait ( 1 )
        self.play ( *_getAnimations ( ) )
        self.remove ( *mob_noteNameGroups, *mob_keyNames )
        self.add ( mob_tableCo5Order1 )
        self.wait ( 0.5 )
        
        def _getAnimations ( ):
            for i, j in enumerate ( acciCountOrder ):
                k = j + 7
                yield Transform ( mob_tableCo5Order1 [ i * 2 ], mob_tableCo5Order2 [ 2 * k ] )
                yield Transform ( mob_tableCo5Order1 [ i * 2 + 1 ], mob_tableCo5Order2 [ 2 * k + 1 ] )
        
        self.play ( *_getAnimations ( ) )
        self.remove ( mob_tableCo5Order1 )
        self.add ( mob_tableCo5Order2 )
        mob_keySigSharps = mob_staff.createKeySig ( clefType, 7, add = False )\
            .after ( mob_clef, 1.5 )
        mob_barline = mob_staff.createBarline ( add = False )\
            .after ( mob_keySigSharps, 6 )
        mob_keySigFlats = mob_staff.createKeySig ( clefType, -7, add = False )\
            .after ( mob_barline, 1.5 )
        self.play ( *( 
            Create ( mob, run_time = 0.5 )
            for mob in ( mob_keySigSharps, mob_barline, mob_keySigFlats )
        ) )
        
        mob_noteNameTextsOnTop = _createNoteNameTexts ( 0, fs = 1.5, buff = 0.4, co5Order = True )\
            .next_to ( mob_staff.mob_staffLines, RIGHT, 1.25 )
        width = mob_noteNameTextsOnTop.get_width ( )
        mob_rightArrow = Line ( ORIGIN, width * RIGHT, color = RED )\
            .next_to ( mob_noteNameTextsOnTop, UP, 0.25 )
        mob_rightArrow.add_tip ( **tipConfig )
        mob_leftArrow = Line ( ORIGIN, width * LEFT, color = GREEN )\
            .next_to ( mob_noteNameTextsOnTop, DOWN, 0.25 )
        mob_leftArrow.add_tip ( **tipConfig )
        mob_sharpSign = MusicGlyph ( "\ue262", musicFont = musicFont, sp = 0.2 )\
            .toPosition ( mob_rightArrow.get_critical_point ( LEFT ) + LEFT * 0.3 )
        mob_flatSign = MusicGlyph ( "\ue260", musicFont = musicFont, sp = 0.2 )\
            .toPosition ( mob_leftArrow.get_critical_point ( RIGHT ) + RIGHT * 0.3 )
        
        self.play (
            Write ( mob_noteNameTextsOnTop, run_time = 1 ),
        )
        self.play (
            LaggedStart ( 
                *(
                    Indicate ( mob, run_time = 0.5 )
                    for mob in mob_noteNameTextsOnTop
                ),
                lag_ratio = 0.5,
            ),
        )
        self.play (
            FadeIn ( mob_sharpSign, run_time = 0.5 ),
            Create ( mob_rightArrow, run_time = 1 ),
        )
        
        self.play (
            LaggedStart ( 
                *(
                    Indicate ( mob, run_time = 0.5 )
                    for mob in reversed ( mob_noteNameTextsOnTop )
                ),
                lag_ratio = 0.5,
            ),
        )
        self.play (
            FadeIn ( mob_flatSign, run_time = 0.5 ),
            Create ( mob_leftArrow, run_time = 1 ),
        )
        
        self.wait ( 2 )

class KeySignatureDisplayScene ( Scene ):
    def construct ( self ):
        clefType = "G"
        def createKeySigStaff ( acciCount: int ) -> Staff:
            mob_staff = Staff ( **staffConfig, staffLength = 12.5 )
            # mob_clef = mob_staff.createClef ( clefType ).setHpos ( 2 )
            # mob_staff.createKeySig ( clefType, acciCount )\
            #     .after ( mob_clef, 1.5 )
            return mob_staff
        
        def createKeySigStaffWithKeyName ( acciCount: int ) -> VGroup:
            mob_staff = createKeySigStaff ( acciCount )
            mob_keyNameText = _createKeyNameText ( acciCount, fs = 1 )\
                .next_to ( mob_staff.mob_staffLines, DOWN, 0.4 )
            return VGroup ( mob_staff, mob_keyNameText )
        
        mob_vg = VGroup ( *( createKeySigStaffWithKeyName ( i ) for i in range ( -7, 8 ) ) )\
            .arrange_in_grid ( cols = 5, buff = ( 0.5, 0.8 ) )\
            .move_to ( UP * 0.25 )
        
        def _getAnimations ( ):
            for mob_staff, _ in mob_vg:
                yield GrowFromPoint ( mob_staff, ORIGIN, run_time = 1 )
        self.play ( *_getAnimations ( ) )
        
        def _getAnimations ( ):
            for i, ( mob_staff, mob_keyNameText ) in enumerate ( mob_vg ):
                mob_clef = mob_staff.createClef ( clefType, add = False ).setHpos ( 2 )
                mob_keySig = mob_staff.createKeySig ( clefType, i - 7, add = False )\
                    .after ( mob_clef, 1.5 )
                yield Write ( mob_keyNameText, run_time = 0.5 )
                yield Succession ( 
                    FadeIn ( mob_clef, run_time = 0.25 ),
                    Create ( mob_keySig, run_time = 0.5 ),
                )
        self.play ( *_getAnimations ( ) )
        
        self.wait ( 5 )

class SemitoneToCircleOfFifthScene ( Scene ):
    def construct ( self ):
        numberCircle1Center = np.array (( -3.25, 0.5, 0 ))
        numberCircle2Center = np.array (( 3.25, 0.5, 0 ))
        co5Order = np.array (( 3, 0, 4, 1, 5, 2, 6 ))
        co5Arg = np.argsort ( co5Order )
        
        def createScaleDegreeLabel ( i: int, mob: NumberCircle, t: float = 1 ):
            return mob.addLabel (
                _majorScale [ i ] * t % 12,
                withOutlineBackground (
                    MathTex ( 
                        rf"\hat{{{i + 1}}}", 
                        **newLatexConfig ( fs = 1.25 ) 
                    ),
                    width = 8,
                ), 
                INSIDE, 0.2,
                add = False,
            ).set_z_index ( 1 )
        
        mob_numberCircle1 = NumberCircle ( maxVal = 12 )\
            .shift ( numberCircle1Center )
        
        mob_numberCircle1.createTicks ( step = 1 )
        mob_numberCircle1.addLabels ( 
            1, 
            lambda x: withOutlineBackground ( 
                MathTex ( rf"\overline{{{x}}}", **latexConfig ),
                width = 8,
            ).set_z_index ( 1 ),
        )
        
        self.play ( Create ( mob_numberCircle1, run_time = 1 ) )
        
        mob_text1_1 = withOutlineBackground ( 
            Text ( "数半音", **newTextConfig ( fs = 2 ) ),
            width = 10,
        )
        mob_text1_2 = withOutlineBackground ( 
            Text ( "音符分布不连续", **textConfig ),
            width = 10,
        ).next_to ( mob_text1_1, DOWN, 0.4 )
        mob_text1_3 = withOutlineBackground ( 
            Text ( "规律不明显", **textConfig ),
            width = 10,
        ).next_to ( mob_text1_2, DOWN, 0.25 )
        VGroup ( mob_text1_1, mob_text1_2, mob_text1_3 )\
            .move_to ( mob_numberCircle1.getPosition ( ) )
        
        # 第一遍，按照数半音的方式构建大调音阶
        
        mob_glowPoints = VGroup ( )
        mob_lines1 = VGroup ( )
        mob_scaleDegreeTexts1 = VGroup ( )
        loopedMajorScale = np.append ( _majorScale, 12 )
        for i in range ( 7 ):
            currentTone, nextTone = loopedMajorScale [ i ], loopedMajorScale [ i + 1 ]
            p1, p2 = mob_numberCircle1.n2p ( currentTone ), mob_numberCircle1.n2p ( nextTone )
            diff = nextTone - currentTone
            isSemitone = ( diff == 1 )
            mob_line = Line (
                p1, p2,
                color = BLUE if isSemitone else RED,
            )
            mob_scaleDegreeText = createScaleDegreeLabel ( i, mob_numberCircle1 )
            
            mob_glowPoint = addGlow ( Dot ( p1, radius = 0.06 ) )
            mob_arc = mob_numberCircle1.createArc ( currentTone, diff, 0.3 )\
                .set_stroke ( color = YELLOW )
            mob_glowPoints.add ( mob_glowPoint )
            mob_lines1.add ( mob_line )
            mob_scaleDegreeTexts1.add ( mob_scaleDegreeText )
            
            addMidi ( self, currentTone + 60 )
            self.play ( 
                FadeIn ( 
                    mob_glowPoint, 
                    mob_scaleDegreeText, 
                    run_time = 0.25 
                ),
                Create ( mob_line, run_time = 0.5 ),
                ShowPassingFlashWithThinningStrokeWidth (
                    mob_arc,
                    time_width = 3,
                    run_time = 0.5,
                ),
            )
        addMidi ( self, 72 )
        
        self.wait ( 0.5 )
        self.play (
            FadeOut ( mob_glowPoints, run_time = 0.5 ),
        )
        self.play  (
            Succession (
                FadeIn ( mob_text1_1, run_time = 0.5 ),
                FadeIn ( mob_text1_2, mob_text1_3, run_time = 0.5 ),
            ),
        )
        self.wait ( 2 )
        
        mob_numberCircle2 = mob_numberCircle1.copy ( )
        self.add ( mob_numberCircle2 )
        
        self.play (
            mob_numberCircle2.animate ( run_time = 1 )\
                .shift ( numberCircle2Center - numberCircle1Center ) 
        )
        
        mob_text2_1 = withOutlineBackground ( 
            Text ( "数五度", **newTextConfig ( fs = 2 ) ),
            width = 10,
        )
        mob_text2_2 = withOutlineBackground ( 
            Text ( "音符固定间隔出现", **textConfig ),
            width = 10,
        ).next_to ( mob_text2_1, DOWN, 0.4 )
        mob_text2_3 = withOutlineBackground ( 
            Text ( "规律明显", **textConfig ),
            width = 10,
        ).next_to ( mob_text2_2, DOWN, 0.25 )
        VGroup ( mob_text2_1, mob_text2_2, mob_text2_3 )\
            .move_to ( mob_numberCircle2.getPosition ( ) )
        
        # 第二遍，按照数五度的方式构建大调音阶
        
        currentTone = 5
        currentDegree = 3
        mob_lines2 = VGroup ( )
        mob_scaleDegreeTexts2 = VGroup ( )
        mob_glowPoints = VGroup ( )
        for i in range ( 6 ):
            nextTone = i * 7 % 12
            mob_line = Line (
                mob_numberCircle2.n2p ( currentTone ),
                mob_numberCircle2.n2p ( nextTone ),
                color = PINK,
            )
            mob_glowPoint = addGlow ( 
                Dot ( 
                    mob_numberCircle2.n2p ( currentTone ), 
                    radius = 0.06 
                ) 
            )
            mob_arc = mob_numberCircle2.createArc ( currentTone, 7, 0.3 )\
                .set_stroke ( color = YELLOW )
            mob_scaleDegreeText = createScaleDegreeLabel ( currentDegree, mob_numberCircle2 )
            mob_glowPoints.add ( mob_glowPoint )
            mob_lines2.add ( mob_line )
            mob_scaleDegreeTexts2.add ( mob_scaleDegreeText )
            self.play (
                FadeIn ( 
                    mob_scaleDegreeText, 
                    mob_glowPoint, 
                    run_time = 0.25 
                ),
            )
            addMidi ( self, currentTone + 60 )
            self.play (
                Create ( mob_line, run_time = 0.5 ),
                ShowPassingFlashWithThinningStrokeWidth (
                    mob_arc,
                    time_width = 3,
                    run_time = 1,
                ),
            )
            currentTone = nextTone
            currentDegree = i * 4 % 7
        mob_glowPoint = addGlow ( Dot ( mob_numberCircle2.n2p ( 11 ), radius = 0.06 ) )
        mob_scaleDegreeText = createScaleDegreeLabel ( 6, mob_numberCircle2 )
        mob_glowPoints.add ( mob_glowPoint )
        mob_scaleDegreeTexts2.add ( mob_scaleDegreeText )
        addMidi ( self, 71 )
        self.play ( FadeIn ( mob_glowPoint, mob_scaleDegreeText, run_time = 0.25 ) )
        self.wait ( 0.5 )
        self.play ( FadeOut ( mob_glowPoints, run_time = 0.5 ) )
        self.play  (
            Succession (
                FadeIn ( mob_text2_1, run_time = 0.5 ),
                FadeIn ( mob_text2_2, mob_text2_3, run_time = 0.5 ),
            ),
        )
        self.wait ( 2 )
        
        # 展示五度音程的特殊性
        
        self.play ( 
            FadeOut (  
                mob_text1_1, mob_text1_2, mob_text1_3,
                mob_text2_1, mob_text2_2, mob_text2_3,
                mob_numberCircle1,
                mob_scaleDegreeTexts1,
                mob_lines1,
                run_time = 0.5,
            ),
            VGroup (
                mob_numberCircle2,
                mob_scaleDegreeTexts2,
                mob_lines2,
            ).animate ( run_time = 1 )\
                .shift ( numberCircle1Center - numberCircle2Center ),
        )
        mob_glowPoints.shift ( numberCircle1Center - numberCircle2Center )
        
        textStartPoint = numberCircle2Center + UP * 2.5
        mob_text1 = Text ( "五度的特殊性", **newTextConfig ( fs = 2 ) )\
            .move_to ( textStartPoint )\
            .align_to ( textStartPoint, UP )
        mob_text2 = Text ( "十二平均律 (12-TET)" , **newTextConfig ( fs = 1.25 ) )\
            .next_to ( mob_text1, DOWN, 0.7 )
        mob_text3 = Text ( "纯八度 = 12 个半音", **newTextConfig ( fs = 1.25 ) )\
            .next_to ( mob_text2, DOWN, 0.35 )
        mob_text4 = Text ( "纯五度 =  7 个半音", **newTextConfig ( fs = 1.25 ) )\
            .next_to ( mob_text3, DOWN, 0.35 )
        mob_text5 = MathTex ( r"\gcd(12, 7) = 1", **newLatexConfig ( fs = 1.25 ) )\
            .next_to ( mob_text4, DOWN, 0.35 )
        mob_text5 [ 0 ] [ 4:6 ].set_color ( GREEN )
        mob_text5 [ 0 ] [ 7:8 ].set_color ( BLUE )
        mob_text6 = Text ( "以 7 为步长可遍历全部 12 个半音", **textConfig )\
            .next_to ( mob_text5, DOWN, 0.4 )
        
        mob_text7 = Text ( 
            "将八度等比分割为 12 份", 
            **newTextConfig ( fs = 1.25 ) 
        ).next_to ( mob_text2, DOWN, 0.35 )
        mob_text8 = Text (
            "八度频率比 1 : 2", 
            **newTextConfig ( fs = 1.25 ),
        ).next_to ( mob_text7, DOWN, 0.35 )
        mob_text9 = MathTex ( 
            r"2^{1/12}", 
            rf"= {np.pow ( 2, 1/12 ):.6f}\dots", 
            **newLatexConfig ( fs = 1.25 ) 
        )
        mob_text10 = MathTex ( 
            r"2^{7/12}",
            rf"= {np.pow ( 2, 7/12 ):.6f}\dots",
            r"\approx \frac{3}{2}",
            **newLatexConfig ( fs = 1.25 ),
        )   .next_to ( mob_text9, DOWN, 0.2 )\
            .align_to ( mob_text9, LEFT )
        VGroup ( mob_text9, mob_text10 )\
            .next_to ( mob_text8, DOWN, 0.35 )
        
        self.play (
            Write ( mob_text1, run_time = 0.5 ),
        )
        self.wait ( 1 )
        self.play (
            FadeIn ( mob_text2, run_time = 0.5 ),
            FadeIn ( mob_text3, run_time = 0.5 ),
        )
        self.wait ( 1 )
        self.play ( 
            FadeIn ( mob_text4, run_time = 0.5 ),
        )
        self.wait ( 1 )
        self.play (
            FadeIn ( mob_text5, run_time = 0.5 ),
        )
        self.wait ( 1 )
        self.play (
            FadeIn ( mob_text6, run_time = 0.5 ),
        )
        
        mob_glowPoints.remove ( mob_glowPoints [ -1 ] )
        self.play ( 
            FadeOut ( mob_scaleDegreeTexts2, run_time = 0.25 ),
        )
        
        # 先把前面已经生成的大调音阶描一遍
        
        self.play ( 
            mob_lines2.animate ( run_time = 0.25 )\
                .set_stroke ( width = 2 ), 
        )  
        for i, ( mob_line, mob_glowPoint ) in enumerate ( zip ( mob_lines2, mob_glowPoints ) ):
            currentTone = ( i - 1 ) * 7 % 12
            mob_arc = mob_numberCircle2.createArc ( currentTone, 7, 0.3 )\
                .set_stroke ( color = YELLOW )
            addMidi ( self, currentTone + 60 )
            self.play (
                ShowPassingFlashWithThinningStrokeWidth (
                    mob_line.copy ( ).set_stroke ( width = 6 ),
                    time_width = 3,
                    run_time = 0.75,
                ),
                ShowPassingFlashWithThinningStrokeWidth (
                    mob_arc,
                    time_width = 3,
                    run_time = 0.75,
                ),
                FadeIn ( mob_glowPoint, run_time = 0.25 ),
                Succession (
                    Wait ( 0.5 ),
                    mob_line.animate ( run_time = 0.25 )\
                        .set_stroke ( width = 4 ),
                )
            )
        
        # 补全五度遍历
        
        currentTone = 11
        mob_extraLines = VGroup ( )
        for i in range ( 6, 12 ):
            nextTone = i * 7 % 12
            mob_line = Line (
                mob_numberCircle2.n2p ( currentTone ),
                mob_numberCircle2.n2p ( nextTone ),
                color = PINK,
            )
            mob_arc = mob_numberCircle2.createArc ( currentTone, 7, 0.3 )\
                .set_stroke ( color = YELLOW )
            mob_glowPoint = addGlow ( 
                Dot ( 
                    mob_numberCircle2.n2p ( currentTone ), 
                    radius = 0.06 
                ) 
            )
            addMidi ( self, currentTone + 60 )
            self.play ( 
                FadeIn ( mob_glowPoint, run_time = 0.25 ),
                Create ( mob_line, run_time = 0.75 ),
                ShowPassingFlashWithThinningStrokeWidth (
                    mob_arc,
                    time_width = 3,
                    run_time = 0.75,
                ),
            )
            mob_glowPoints.add ( mob_glowPoint )
            mob_extraLines.add ( mob_line )
            currentTone = nextTone
        addMidi ( self, 65 )
        self.play (
            *(
                FadeOut ( mob, run_time = 0.5 ) 
                for mob in mob_glowPoints 
            ),
        )
        self.wait ( 1 )
        self.play ( 
            *(
                mob.animate ( run_time = 0.25 )\
                    .set_stroke ( opacity = 0.3 )
                for mob in mob_extraLines
            ),
            *(
                FadeIn ( mob, run_time = 0.25 )
                for mob in mob_scaleDegreeTexts2
            ),
        )
        
        mob_lines2.add ( *mob_extraLines )
        
        self.wait ( 2 )
        self.play (
            FadeOut (
                mob_text3, mob_text4, mob_text5, mob_text6,
                run_time = 0.5,
            )
        )
        self.play ( FadeIn ( mob_text7, run_time = 0.5 ) )
        self.wait ( 0.5 )
        self.play ( FadeIn ( mob_text8, run_time = 0.5 ) )
        self.wait ( 0.5 )
        
        mob_arc = mob_numberCircle2.createArc ( 0, 1, 0.3 )\
            .set_stroke ( color = YELLOW )
        
        self.play ( 
            FadeIn ( mob_text9, run_time = 0.5 ),
            ShowPassingFlashWithThinningStrokeWidth (
                mob_arc,
                time_width = 5,
                run_time = 2,
            )
        )
        self.wait ( 0.5 )
        
        mob_arc = mob_numberCircle2.createArc ( 0, 7, 0.3 )\
            .set_stroke ( color = YELLOW )
        
        self.play ( 
            FadeIn ( mob_text10, run_time = 0.5 ),
            ShowPassingFlashWithThinningStrokeWidth (
                mob_arc,
                time_width = 5,
                run_time = 3,
            )
        )
        
        self.wait ( 2 )
        
        self.play (
            FadeOut (
                mob_text1,mob_text2,
                mob_text7,mob_text8,
                mob_text9,mob_text10,
                run_time = 0.25,
            )
        )
        
        mob_semitoneCircleText = withOutlineBackground (
            Text (
                "半音圈",
                **newTextConfig ( fs = 2 ),
            ).set_z_index ( 1 )
        ).move_to ( numberCircle1Center )
        mob_circleOfFifthText = withOutlineBackground (
            Text (
                "五度圈",
                **newTextConfig ( fs = 2 ),
            ).set_z_index ( 1 )
        ).move_to ( numberCircle2Center )
        
        self.play (
            FadeIn ( 
                mob_semitoneCircleText, 
                run_time = 0.5 
            ),
        )
        
        mob_numberCircle3 = mob_numberCircle2.copy ( )
        mob_lines3 = mob_lines2.copy ( )
        mob_scaleDegreeTexts3 = mob_scaleDegreeTexts2.copy ( )
        self.add ( mob_numberCircle3, mob_lines3 )
        self.play ( *(
            mob.animate ( run_time = 1 )\
                .shift ( numberCircle2Center - numberCircle1Center )
            for mob in ( 
                mob_numberCircle3, 
                mob_lines3, 
                mob_scaleDegreeTexts3,
            )
        ) )
        
        mob_glowPoint = addGlow ( Dot ( 
            mob_numberCircle3.n2p ( 1 ), 
            radius = 0.06
        ) )
        mob_arc = mob_numberCircle3.createArc ( 1, 6, 0.3 )\
            .set_stroke ( color = YELLOW )
        self.play ( FadeIn ( mob_glowPoint, run_time = 0.25 ) )
        
        var_t = ValueTracker ( 1 )
        
        def updateNumberCircle ( mob: NumberCircle ):
            mob_labels = mob [ -1 ]
            mob_ticks = mob [ -2 ]
            t = var_t.get_value ( )
            for i, ( mob_label, mob_tick, mob_line ) in \
                    enumerate ( zip ( mob_labels, mob_ticks, mob_lines3 ) ):
                val = i * t % 12
                mob_tick.become ( mob.createTick ( val, add = False ) )
                mob.addLabel ( val, mob_label, add = False )
            
            for i, mob_scaleDegreeText in enumerate ( mob_scaleDegreeTexts3 ):
                tone = ( i - 1 ) * 7 % 12
                val = tone * t % 12
                mob.addLabel ( 
                    val, mob_scaleDegreeText, 
                    side = INSIDE,
                    buff = 0.2, 
                    add = False,
                )
            
            val = 5 * t % 12
            for i , mob_line in enumerate ( mob_lines3 ):
                nextTone = i * 7 % 12
                nextVal = nextTone * t % 12
                p1 = mob_numberCircle3.n2p ( val )
                p2 = mob_numberCircle3.n2p ( nextVal )
                mob_line.put_start_and_end_on ( p1, p2 )
                val = nextVal
        
        mob_numberCircle3.add_updater ( updateNumberCircle )
        
        self.play (
            var_t.animate\
                .set_value ( 7 ),
            Rotate ( 
                mob_glowPoint, 
                angle = -PI,
                about_point = mob_numberCircle3.getPosition ( ),
            ),
            Create ( mob_arc ),
            run_time = 3,
            rate_func = rf.ease_in_out_cubic,
        )
        
        mob_numberCircle3.clear_updaters ( )
        
        self.play (
            Uncreate ( mob_arc.reverse_points ( ), run_time = 0.5 ),
            FadeOut ( mob_glowPoint, run_time = 0.25 ),
        )
        self.play (
            FadeIn ( 
                mob_circleOfFifthText, 
                run_time = 0.5 
            ),
        )
        
        # 按照五度圈顺序遍历大调音阶
        for i, mob_scaleDegreeText in \
                zip ( range ( -1, 6 ), mob_scaleDegreeTexts3 ):
            tone = i * 7 % 12
            addMidi ( self, tone + 60 )
            self.play ( 
                Indicate ( 
                    mob_scaleDegreeText, 
                    scale_factor = 2,
                    run_time = 0.5,
                ),
            )
        self.wait ( 1 )
        
        # 按照音级数顺序遍历大调音阶
        for i in range ( 7 ):
            tone = _majorScale [ i ]
            arg = co5Arg [ i ]
            mob_scaleDegreeText = mob_scaleDegreeTexts3 [ arg ]
            addMidi ( self, tone + 60 )
            self.play ( 
                Indicate ( 
                    mob_scaleDegreeText, 
                    scale_factor = 2,
                    run_time = 0.5,
                ),
            )
        self.wait ( 2 )

class DividingCircleScene ( Scene ):
    def construct ( self ):
        m = 12
        circleCenter = np.array (( -3.25, 0.5, 0 ))
        textStartPoint = np.array (( 3, 2.75, 0 )) #(( 0.5, 2.75, 0 ))
        
        def createNumberCircle ( maxVal: float ) -> NumberCircle:
            mob_numberCircle = NumberCircle ( maxVal = maxVal )\
                .shift ( circleCenter )
            mob_ticks = mob_numberCircle.createTicks ( )
            mob_labels = mob_numberCircle.addLabels ( 1, lambda x: 
                TextWithBackground ( 
                    MathTex ( 
                        r"\overline{%d}" % x, 
                        **latexConfig 
                    ) 
                ).set_z_index ( 1 ),
            )
            return mob_numberCircle, mob_ticks, mob_labels
        
        var_m = ValueTracker ( 0 )
        mob_numberCircle = always_redraw ( lambda: 
            createNumberCircle ( var_m.get_value ( ) ) [ 0 ] 
        )
        mob_groupSymbol = MathTex ( 
            r"\frac{\mathbb{Z}}{%d\mathbb{Z}}" % m,
            **newLatexConfig ( fs = 3 ),
        ).shift ( circleCenter )
        mob_groupSymbol [ 0 ] [ 2:-1 ].set_color ( GREEN )
        
        self.play ( Create ( mob_numberCircle, run_time = 1 ) )
        self.play (
            var_m.animate ( run_time = 2, rate_func = rf.ease_out_cubic )\
                .set_value ( m )
        )
        
        mob_numberCircle.clear_updaters ( )
        self.remove ( mob_numberCircle )
        mob_numberCircle, _, mob_labels = createNumberCircle ( m )
        self.add ( mob_numberCircle )
        
        self.play ( Write ( mob_groupSymbol, run_time = 0.5 ) )
        self.wait ( 0.5 )
        
        mob_temp = MathTex (
            r"\mathbb{Z}_{%d}" % m,
            **newLatexConfig ( fs = 6 ),
        ).shift ( circleCenter ).set_z_index ( -1 )
        mob_temp [ 0 ] [ 1: ].set_color ( GREEN )
        
        self.play (
            Transform (
                mob_groupSymbol,
                mob_temp,
                run_time = 0.5,
            )
        )
        
        self.remove ( mob_groupSymbol )
        mob_groupSymbol = mob_temp
        self.add ( mob_groupSymbol )
        
        self.wait ( 1 )
        
        def animateCircleDivision ( k: int ): 
            gcdmk = np.gcd ( m, k )
            n = m // gcdmk
            traverseOrder = ( np.arange ( n ) * k ) % m
            print ( traverseOrder )
            last = 0
            
            mob_glowPoints = VGroup ( )
            mob_lines = VGroup ( )
            
            # m, k 及其最大公约数
            mob_gcdText = VGroup (
                MathTex ( "m", "=", str ( m ), **newLatexConfig ( fs = 1.25 ) ),
                MathTex ( "k", "=", str ( k ), **newLatexConfig ( fs = 1.25 ) ),
                MathTex ( r"\gcd (m, k) = ", str ( gcdmk ), **newLatexConfig ( fs = 1.25 ) ),
            ).arrange_in_grid ( rows = 1, buff = 0.6 )\
                .move_to ( textStartPoint )\
                .align_to ( textStartPoint, DOWN )
            mob_gcdText [ 0 ] [ 0 ].set_color ( GREEN )
            mob_gcdText [ 1 ] [ 0 ].set_color ( BLUE )
            mob_gcdText [ 2 ] [ 0 ] [ 0:3 ].set_color ( LIGHT_PINK )
            mob_gcdText [ 2 ] [ 0 ] [ 4 ].set_color ( GREEN )
            mob_gcdText [ 2 ] [ 0 ] [ 6 ].set_color ( BLUE )
            
            # k, 2k, ..., (m - 1) k 模 m 的余数
            mob_modulusTexts = VGroup ( )
            
            for i in range ( n if gcdmk == 1 else n + 1 ):
                mob_modulusText = MathTex ( 
                    r"{i} \times {{{{ \overline{{{k}}} }}}} = \overline{{{rem}}}"\
                        .format ( 
                            i = i, k = k, m = m, 
                            rem = i * k % m 
                        ),
                    **newLatexConfig ( ),
                )
                mob_modulusText [ 1 ] [ 1: ].set_color ( BLUE )
                mob_modulusTexts.add ( mob_modulusText )
            mob_modulusTexts.arrange_in_grid ( 
                cols = 2, buff = ( 0.6, 0.4 ),
                col_alignments = "ll"
            )   .next_to ( mob_gcdText, DOWN, 0.5 )\
                .align_to ( mob_gcdText, LEFT )\
                .shift ( RIGHT * 1.4 )
            
            # 由 k 生成的循环子群
            if gcdmk == 1:
                mob_subgroupText = MathTex (
                    rf"\langle\,\overline{{{k}}}\,\rangle = ",
                    rf"\mathbb{{Z}}_{{{m}}}" ,
                    **newLatexConfig ( fs = 1.25 )
                ).next_to ( mob_modulusTexts, DOWN, 0.5 )
                mob_subgroupText [ -1 ] [ 1: ].set_color ( GREEN )
            else:
                mob_subgroupText = MathTex (
                    rf"\langle\,\overline{{{k}}}\,\rangle = ",
                    rf"\frac{{{gcdmk}\mathbb{{Z}}}}{{{m}\mathbb{{Z}}}} \cong",
                    rf"\mathbb{{Z}}_{{{n}}}",
                    **newLatexConfig ( fs = 1.25 )
                ).next_to ( mob_modulusTexts, DOWN, 1 )
                mob_subgroupText [ 1 ] [ : len ( str ( gcdmk ) ) ]\
                    .set_color ( LIGHT_PINK )
                mob_subgroupText [ 1 ] [ -3 - len ( str ( m ) ) : -3 ]\
                    .set_color ( GREEN )
            
            mob_subgroupText [ 0 ] [ 2:-2 ].set_color ( BLUE )
            
            self.play ( Write ( mob_gcdText, run_time = 0.5 ) )
            self.play (
                mob_groupSymbol.animate ( run_time = 0.5 )\
                    .set_fill ( opacity = 0.15 ),
                Circumscribe ( mob_labels [ 0 ], time_width = 2 ),  
            )
                
            for current, mob_modulusText in zip ( np.roll ( traverseOrder, -1 ), mob_modulusTexts ):
                self.play ( Write ( mob_modulusText, run_time = 0.5 ) )
                endPoint = mob_numberCircle.n2p ( current )
                mob_point = addGlow ( Dot ( radius = 0.06 ).move_to ( endPoint ) )
                mob_line = mob_numberCircle.createLine ( last, current, color = RED )
                mob_arc = mob_numberCircle.createArc ( last, k, color = YELLOW, buff = 0.3 )
                mob_glowPoints.add ( mob_point )
                mob_lines.add ( mob_line )
                self.play (
                    ShowPassingFlashWithThinningStrokeWidth ( 
                        mob_arc, time_width = 3, 
                        run_time = 1.5 
                    ),
                    Succession (
                        Wait ( 1 ),
                        FadeIn ( mob_point, run_time = 0.25 ),
                    ),
                    Create ( mob_line, run_time = 0.75 ),
                )
                last = current
            
            if gcdmk > 1:
                self.play ( 
                    Write ( mob_modulusTexts [ -1 ], run_time = 0.5 ) 
                )
            
            self.play (
                FadeOut ( mob_glowPoints, run_time = 0.5 ),
            )
            
            for i, j in enumerate ( np.argsort ( traverseOrder ) ):
                self.play (
                    Indicate ( 
                        mob_labels [ i * gcdmk ].original, 
                        scale_factor = 2 
                    ),
                    Indicate ( mob_modulusTexts [ j ] ),
                    run_time = 0.5,
                )
            
            self.play ( 
                Succession (
                    FadeIn ( mob_subgroupText, run_time = 0.5 ),
                    Circumscribe ( 
                        mob_subgroupText, 
                        time_width = 2, 
                        run_time = 1 
                    ),
                )
            )
            self.wait ( 2 )
            
            # 清除画面中所有多余对象
            self.play (
                FadeOut (
                    mob_gcdText,
                    mob_modulusTexts, 
                    mob_subgroupText, 
                    mob_lines,
                )
            )
        
        animateCircleDivision ( 7 )
        animateCircleDivision ( 9 )
        animateCircleDivision ( 10 )
        self.wait ( 2 )

class DividingOctaveScene ( Scene ):
    def construct ( self ):
        def getBoundLabels ( ) -> Mapping [ float, Mobject ]:
            return {
                0: TextWithBackground ( MathTex ( "1", **latexConfig ) ).set_z_index ( 1 ),
                1: TextWithBackground ( MathTex ( "2", **latexConfig ) ).set_z_index ( 1 ),
            }
        
        numberLineBuff = 0.1
        numberLineLength = 12
        largeTickSize = 0.15
        numberLinePosition = np.array ( ( 0, 1.6, 0 ) )
        auxNumberLinePosition = np.array ( ( 0, -1.4, 0 ) )
        
        mob_note = Text (
            "注：以下图中采用的坐标轴都是对数轴",
            **textConfig
        ).to_corner ( UL, buff = 0.25 )
        mob_tex1 = MathTex ( 
            r"f_n = \frac{3^n}{2^{\lfloor n \log_2 3 \rfloor}}",
            **newLatexConfig ( fs = 2 ), 
        )
        mob_tex2 = MathTex (
            r"(n = 0, 1, 2, \cdots)",
            **newLatexConfig ( fs = 1.25 ),
        ).next_to ( mob_tex1, RIGHT, 0.5 )
        VGroup ( mob_tex1, mob_tex2 ).move_to ( DOWN )
        mob_tex1 [ 0 ] [ 3 ].set_color ( RED )
        mob_tex1 [ 0 ] [ 6 ].set_color ( GREEN )
        # self.add ( index_labels ( mob_tex1 [ 0 ] ) )
        mob_numberLine = NumberLine (
            x_range = ( -numberLineBuff, 1 + numberLineBuff ),
            length = numberLineLength,
            include_ticks = False,
            font_size = latexFs ( 1 ), 
        )   .add_labels ( getBoundLabels ( ) )\
            .shift ( numberLinePosition )
        mob_numberLine.add (
            mob_numberLine.get_tick ( 0, largeTickSize ),
            mob_numberLine.get_tick ( 1, largeTickSize ),
        )
        
        # 展示五度相生律的生成过程
        
        self.play (
            FadeIn ( mob_note, run_time = 0.25 ),
            Create ( mob_numberLine, run_time = 1 ),
        )
        self.play (
            Succession (
                Write ( mob_tex1, run_time = 0.5 ),
                FadeIn ( mob_tex2, run_time = 0.25 ),
            )
        )
        self.play ( 
            Circumscribe ( 
                mob_tex1 [ 0 ] [ 3 ],
                time_width = 2,
            ) 
        )
        self.play ( 
            Circumscribe ( 
                mob_tex1 [ 0 ] [ 6 ],
                time_width = 2,
            ) 
        )
        self.wait ( 1 )
        
        self.play ( 
            FadeOut ( mob_tex1, mob_tex2, run_time = 0.5 ) 
        )
        
        n = m = 1
        p = lastP = 0
        lastRatio = Q ( 1 )
        
        def auxNumberLineSetup ( mob: NumberLine, direction = UP ) -> None:
            log2LastRatio = np.log2 ( float ( lastRatio ) )
            mob.add_labels ( getBoundLabels ( ) )\
                .add_labels ( 
                    { 
                        log2LastRatio: ( mob_label := TextWithBackground ( MathTex ( 
                            frac2Latex ( lastRatio ), 
                            **latexConfig 
                        ) ) )
                    },
                    direction = direction,
                )\
                .add (
                    mob.get_tick ( 0, largeTickSize ),
                    mob.get_tick ( 1, largeTickSize ),
                    ( mob_tick := mob.get_tick ( log2LastRatio ) ),
                )
            return mob_label, mob_tick
        
        # 创建新数轴
        mob_auxNumberLine = NumberLine (
            length = numberLineLength,
            x_range = ( -numberLineBuff, 1 + numberLineBuff ),
            include_ticks = False,
            font_size = latexFs ( 1 ), 
        ).shift ( numberLinePosition )
        auxNumberLineSetup ( mob_auxNumberLine, DOWN )
        
        for i in range ( 11 ):
            n *= 3
            m, p = prevPowerOf2 ( n )
            
            # 上一个音的频率乘 3
            unscaledRatio = lastRatio * 3
            
            # 上一个音的频率乘 3 再移至一个八度内
            ratio = Q ( n, m )
            
            # 需要除以 2 的次数
            divideTimes = p - lastP
            
            # 频率的对数值，因为采用对数轴
            log2UnscaledRatio = np.log2 ( float ( unscaledRatio ) )
            log2Ratio = np.log2 ( float ( ratio ) )
            log2LastRatio = np.log2 ( float ( lastRatio ) )
            
            # 新建一个数轴用于展示频率乘 3 再除以 2 的幂次的过程
            
            # 将新数轴移动到画面下方并做适当缩放
            mob_temp = NumberLine ( 
                length = numberLineLength,
                x_range = ( -numberLineBuff, log2UnscaledRatio + numberLineBuff ),
                include_ticks = False,
                font_size = latexFs ( 1 ), 
            ).shift ( auxNumberLinePosition )
            auxNumberLineSetup ( mob_temp )
            
            self.play ( 
                Transform ( mob_auxNumberLine, mob_temp ),
            )
            self.remove ( mob_auxNumberLine )
            mob_auxNumberLine = mob_temp
            self.add ( mob_auxNumberLine )
            
            mob_unscaledRatioTick = mob_auxNumberLine.get_tick ( log2UnscaledRatio )
            mob_unscaledRatioLabel = TextWithBackground ( 
                MathTex ( frac2Latex ( unscaledRatio ), **latexConfig ) 
            )
            mob_auxNumberLine.add_labels ( 
                { log2UnscaledRatio: mob_unscaledRatioLabel },
                direction = UP,
            )
            mob_auxNumberLine.add ( mob_unscaledRatioTick )
            
            # 向右的箭头
            mob_arrowForward = CurvedArrow (  
                mob_auxNumberLine.n2p ( log2LastRatio ),
                mob_auxNumberLine.n2p ( log2UnscaledRatio ),
                angle = -PI / 4,
                color = RED,
            ).set_z_index ( -1 )
            mob_mul3 = MathTex ( 
                "\\times 3", 
                **newLatexConfig ( fs = 1.25 ), 
                color = RED 
            ).next_to ( mob_arrowForward, UP, 0.2 )
            
            self.play (
                Create ( mob_arrowForward, run_time = 1 ),
                FadeIn ( mob_mul3, run_time = 0.25 ),
                Create ( mob_unscaledRatioLabel, run_time = 0.25 ),
                Create ( mob_unscaledRatioTick, run_time = 0.25 ),
                Flash ( mob_unscaledRatioTick, run_time = 1 ),
            )
            
            mob_auxRatioLabel = TextWithBackground ( MathTex ( frac2Latex ( ratio ), **latexConfig ) )
            mob_auxRatioTick = mob_auxNumberLine.get_tick ( log2Ratio )
            mob_auxNumberLine.add_labels ( 
                { log2Ratio: mob_auxRatioLabel },
                direction = UP,
            )
            mob_auxNumberLine.add ( mob_auxRatioTick )

            # 在主数轴上展示新生成的音符
            
            mob_arrowBackwards = VGroup (
                CurvedArrow (  
                    mob_auxNumberLine.n2p ( log2UnscaledRatio - i ),
                    mob_auxNumberLine.n2p ( log2UnscaledRatio - i - 1 ),
                    angle = -PI / 4,
                    color = GREEN,
                ) for i in range ( divideTimes )
            )
            mob_div2Texts = VGroup (
                MathTex ( 
                    "\\times 1/2", 
                    **newLatexConfig ( fs = 1.25 ), 
                    color = GREEN 
                ).next_to ( mob, DOWN, 0.2 )
                for mob in mob_arrowBackwards
            )
            
            mob_ratioLabel = MathTex ( frac2Latex ( ratio ), **latexConfig )
            mob_ratioTick = mob_numberLine.get_tick ( log2Ratio )
            mob_numberLine.add_labels ( 
                { log2Ratio: mob_ratioLabel },
                direction = DOWN if i < 6 else UP,
            )
            mob_numberLine.add ( mob_ratioTick )
            
            self.play (
                Succession (
                    *( 
                        Create ( mob ) 
                        for mob in mob_arrowBackwards 
                    ),
                    run_time = 1,
                ),
                Succession (
                    *( 
                        FadeIn ( mob, run_time = 0.25 ) 
                        for mob in mob_div2Texts 
                    ),
                ),
                Create ( mob_ratioLabel, run_time = 1 ),
                Create ( mob_ratioTick, run_time = 1 ),
                Flash ( mob_ratioTick, run_time = 1 ),
                Create ( mob_auxRatioLabel, run_time = 1 ),
                Create ( mob_auxRatioTick, run_time = 1 ),
                Flash ( mob_auxRatioTick, run_time = 1 ),
            )
            self.wait ( 1 )
            self.play ( 
                FadeOut ( 
                    mob_arrowForward, mob_mul3,
                    mob_arrowBackwards, mob_div2Texts,
                    run_time = 0.25 
                ), 
            )
            
            lastRatio, lastP = ratio, p
            
            mob_temp2 = NumberLine ( 
                length = numberLineLength,
                x_range = ( -numberLineBuff, log2UnscaledRatio + numberLineBuff ),
                include_ticks = False,
                font_size = latexFs ( 1 ), 
            ).shift ( auxNumberLinePosition )
            auxNumberLineSetup ( mob_temp2 )
            
            self.remove ( mob_auxNumberLine, mob_arrowForward )
            mob_auxNumberLine = mob_temp2
            self.add ( mob_auxNumberLine )
            
        self.wait ( 2 )
        
class CircleOfFifthScene ( Scene ):
    def construct ( self ):
        self.camera.background_color = "#282c34"
        
        sharpKeys = (
            "C 大调",
            "G 大调",
            "D 大调",
            "A 大调",
            "E 大调",
            "B 大调",
            r"{\sh}F 大调",
            r"{\sh}C 大调",
        )
        flatKeys = (
            "C 大调",
            "F 大调",
            r"{\fl}B 大调",
            r"{\fl}E 大调",
            r"{\fl}A 大调",
            r"{\fl}D 大调",
            r"{\fl}G 大调",
            r"{\fl}C 大调",
        )
        
        clefType = "G"
        clefPos = 2
        clefKeySigPad = 1.5
        keySigScalePad = 2.5
        
        mob_keyboard: VGroup = MultiOctavePianoKeyboard ( 
            whiteWidth = 0.42,
            whiteHeight = 2.25,
            blackWidth = 0.21,
            blackHeight = 1.25,
        ).to_corner ( UR, buff = 0 )\
            .shift ( ( -0.6, -0.75, 0 ) )
        mob_circleOfFifth: VGroup = CircleOfFifth ( )\
            .to_corner ( UL )
        mob_scaleDegreeRing = ScaleDegreeRing ( 
            radius = mob_circleOfFifth.r3,
            layerThickness = 1,
        ).shift ( mob_circleOfFifth.getPosition ( ) )
        
        mob_staff: VGroup = Staff ( 
            **staffConfig,
            staffLength = 32,
        ).next_to ( mob_keyboard, DOWN, 0.75 )
        mob_clef = mob_staff.createClef ( clefType ).setHpos ( clefPos )
        mob_keySig = mob_staff.createKeySig ( 
            clefType, 0, add = False,
        ).after ( mob_clef, clefKeySigPad )
        
        mob_keySigIndicator = KeySigIndicator ( 
            width = mob_keyboard.get_width ( )
        ).next_to ( mob_staff.mob_staffLines, DOWN, 0.75 )
        
        def createKeyNameText ( i: int ) -> Text:
            return Tex ( 
                sharpKeys [ i ] if i >= 0 else flatKeys [ -i ], 
                **newLatexConfig ( fs = 1.5 ),
            ).next_to ( mob_keySigIndicator, DOWN, 0.5 )
        mob_keyNameText = createKeyNameText ( 0 )
        
        self.play ( 
            Create ( mob_circleOfFifth ),
            Create ( mob_scaleDegreeRing ),
            Create ( mob_keyboard ),
            Create ( mob_staff ),
            Create ( mob_keySigIndicator ),
            run_time = 0.5,
        )
        self.play (
            mob_circleOfFifth.var_rotation.animate\
                .set_value ( TAU * 3 ),
            run_time = 3,
        )
        self.wait ( 2 )
        
        def animateKeyChange ( acciCount: int ):
            tonic = acciCount * 7 % 12
            startDegree = acciCount * 4 % 7
            if acciCount >= 0:
                changedKeys = frozenset (  
                    np.arange ( 6 - acciCount, 6 ) * 4 % 7
                )
                keyMarkColor = MARK_RED
                noteMarkColor = RED
            else:
                changedKeys = frozenset (  
                    np.arange ( -1, -1 - acciCount ) * 4 % 7
                )
                keyMarkColor = MARK_GREEN
                noteMarkColor = GREEN
            mob_newKeySig = mob_staff.createKeySig ( 
                clefType, acciCount, add = False, 
            ).after ( mob_clef, clefKeySigPad )
            scaleNotePositions = np.arange ( 7 ) + ( startDegree - 6 )
            if acciCount == -7: scaleNotePositions += 7
            mob_scale = mob_staff.createScale ( 
                scaleNotePositions, 
                noteheadType = it.chain ( ( "whole", ), it.repeat ( "black" ) ),
                buff = 1.25,
                add = False,  
            ).after ( mob_newKeySig, keySigScalePad )
            self.play (
                # 五度圈旋转到对应位置
                mob_circleOfFifth.animateRotateToIdx ( acciCount, run_time = 0.5 ),
                # 调号切换
                Transform ( 
                    mob_keySig, mob_newKeySig, 
                    run_time = 0.5 
                ),
                # 调性名称切换
                Transform (
                    mob_keyNameText,
                    createKeyNameText ( acciCount ),
                    run_time = 0.25,
                ),
                # 升降号数量指示条切换
                mob_keySigIndicator.animate ( run_time = 0.25 )\
                    .setAcciCount ( acciCount )
            )
            # 由于不明原因，使用动画添加高亮会严重拖慢渲染进度
            # 所以此处改为瞬间改变五度圈的状态但不添加动画效果
            for i, ( tone, mob_note ) in enumerate ( zip ( _majorScale, mob_scale ) ):
                if i in changedKeys:
                    mob_note [ -1 ].set_color ( noteMarkColor )
                transposedTone = tone + tonic
                midiNote = transposedTone + 60
                # mob_scaleDegreeSector = mob_scaleDegreeRing.getSectorByDegree ( i )
                
                addMidi ( self, midiNote )
                # 高亮五度圈区域
                mob_circleOfFifth.getSectorByKeyAcciAndDegree ( acciCount, i )\
                    .highlight ( )
                # 钢琴键盘上对应的琴键着色
                # 有变音记号的琴键着特殊颜色 (升号为红色，降号为绿色)
                mob_keyboard\
                    .markKey ( 
                        transposedTone, 
                        markColor = ( 
                            keyMarkColor if i in changedKeys 
                            else MARK_BLUE 
                        ),
                    ),
                self.add ( mob_note )
                self.wait ( 0.5 )
            self.wait ( 1 )
            mob_circleOfFifth.clearHighlight ( )
            self.play (
                *(
                    FadeOut ( mob, run_time = 0.25 )
                    for mob in mob_scale
                ),
                mob_keyboard.animate ( run_time = 0.25 )\
                    .resetMarks ( ),
            )
        
        animateKeyChange ( 0 )
        # 正向遍历五度圈，获得升号调
        for i in range ( 1, 8 ): animateKeyChange ( i )
        self.wait ( 1 )
        animateKeyChange ( 0 )
        # 反向遍历五度圈，获得降号调
        for i in range ( 1, 8 ): animateKeyChange ( -i )

        self.wait ( 3 )
        
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
#######################################################