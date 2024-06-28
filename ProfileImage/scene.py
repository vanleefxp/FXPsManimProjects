from manim import *

class ProfileImageScene ( Scene ):
    def construct ( self ):
        self.camera.background_color = ManimColor.from_hex ( "#333333" )
        tex = MathTex ( r"\mathbb{F}[x]_p", font_size = 216 )
        self.add ( tex )