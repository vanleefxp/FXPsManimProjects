from pathlib import Path

from manim import TexTemplate
import pyrsistent as p

__all__ = [ 
    "textConfig", "latexConfig", 
    "newTextConfig", "newLatexConfig",
    "textFs", "latexFs",
]   

DIR = Path ( __file__ ).parent if "__file__" in locals ( ) else Path.cwd ( )

BASE_FONT_SIZE = 25
LATEX_FONT_SIZE_MULTIPLIER = 1.28

textConfig = p.m (
    font = "FandolSong", # "CEF Fonts CJK",
    font_size = BASE_FONT_SIZE,
)

latexTemplate = TexTemplate (
    tex_compiler = "xelatex",
    output_format = ".xdv",
    preamble = ( DIR/"assets/preamble.tex" )\
        .read_text ( encoding = "utf-8" ),
)

latexConfig = p.m (
    font_size = BASE_FONT_SIZE * LATEX_FONT_SIZE_MULTIPLIER,
    tex_template = latexTemplate,
)

def textFs ( fs = 1 ):
    return BASE_FONT_SIZE * fs

def latexFs ( fs = 1 ):
    return BASE_FONT_SIZE * LATEX_FONT_SIZE_MULTIPLIER * fs

def newTextConfig ( 
    fs = 1,
    **kwargs 
):
    return textConfig.update (
        {
            "font_size": textFs ( fs ),
            **kwargs,
        }
    )

def newLatexConfig ( 
    fs = 1,
    **kwargs 
):
    fontSize = BASE_FONT_SIZE * LATEX_FONT_SIZE_MULTIPLIER * fs
    return latexConfig.update (
        {
            "font_size": latexFs ( fs ),
            **kwargs,
        }
    )
