from collections.abc import Mapping
from typing import Any
import os, json 
from pathlib import Path
from dataclasses import dataclass

from manim import *
from manim.typing import Vector3D

@dataclass
class SubtitleLine ( ):
    content: str
    startTime: int = None
    endTime: int = None

class SubtitleScene ( Scene ):
    def __init__ ( 
            self, subtitleFile: os.PathLike, /,
            latexConfig: Mapping [ str, Any ] = None,
            subtitlePosition: Vector3D = DOWN, 
            subtitleBuff: float = 0.1, 
            **kwargs 
    ):
        subtitleFile = Path ( subtitleFile )
        subtitleData = json.loads ( subtitleFile.read_text ( encoding = "utf-8" ) )
        if latexConfig is not None:
            self._latexConfig = latexConfig
        else:
            self._latexConfig = { }
        self._data = [ ]
        for line in subtitleData:
            self._data.append ( SubtitleLine ( **line ) )
        self._subtitlePosition = subtitlePosition
        self._subtitleBuff = subtitleBuff
    
    def construct ( self ):
        for i, line in enumerate ( self._data ):
            mob_subtitle = Tex ( line.content, **self._latexConfig )\
                .to_corner ( self._subtitlePosition, buff = self._subtitleBuff )
            mob_subtitleBg = SurroundingRectangle ( mob_subtitle, buff = 0.1 )\
                .set_fill ( color = BLACK, opacity = 0.5 )
            mob_subtitle = VGroup ( mob_subtitleBg, mob_subtitle )
            self.add ( mob_subtitle )
            start, end = line.startTime, line.endTime
            if end is not None:
                self.wait ( end - start )
                self.remove ( mob_subtitle )
                if i < len ( self._data ) - 1:
                    nextLine = self._data [ i + 1 ]
                    nextStart = nextLine.startTime
                    self.wait ( nextStart - end )
            else:
                nextLine = self._data [ i + 1 ]
                nextStart = nextLine.startTime
                self.wait ( nextStart - start )