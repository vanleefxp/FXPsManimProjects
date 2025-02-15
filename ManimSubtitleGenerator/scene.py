from pathlib import Path
import json 

from manim import *
from subtitle_generator import SubtitleLine

DIR = Path ( __file__ ).parent if "__file__" in locals ( ) else Path.cwd ( )

latexTemplate = TexTemplate (
    tex_compiler = "xelatex",
    output_format = ".xdv",
    preamble = ( DIR/"assets/preamble.tex" ).read_text ( ),
)

latexConfig = {
    "font_size": 32,
    "tex_template": latexTemplate,
}

class SubtitleScene ( Scene ):
    def construct ( self ):
        data = [ ]
        for lineData in json.loads ( ( DIR/"assets/sub.json" ).read_text ( encoding = "utf-8" ) ):
            data.append ( SubtitleLine ( **lineData ) )
        
        mob_subtitle = None
        for i, line in enumerate ( data ):
            print ( f"Line {i+1}: {line.content}" )
            if mob_subtitle is not None:
                self.remove ( mob_subtitle )
            mob_subtitle = Tex ( line.content, **latexConfig )\
                .to_corner ( DOWN, buff = 0.1 )
            mob_subtitleBg = SurroundingRectangle ( mob_subtitle, buff = 0.2 )\
                .set_fill ( color = BLACK, opacity = 0.5 )\
                .set_stroke ( width = 0, opacity = 0 )  
            mob_subtitle = VGroup ( mob_subtitleBg, mob_subtitle )
            self.add ( mob_subtitle )
            start, end = line.startTime, line.endTime
            if end is not None:
                self.wait ( ( end - start ) / 1000 )
                self.remove ( mob_subtitle )
                if i < len ( data ) - 1:
                    nextLine = data [ i + 1 ]
                    nextStart = nextLine.startTime
                    self.wait ( ( nextStart - end ) / 1000 )
            else:
                nextLine = data [ i + 1 ]
                nextStart = nextLine.startTime
                self.wait ( ( nextStart - start ) / 1000 )