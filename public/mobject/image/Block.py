from pathlib import Path

from manim import *

DIR = Path ( __file__ ).parent if "__file__" in locals ( ) else Path.cwd ( )

__all__ = [ "NoteBlock" ]

class NoteBlock ( ImageMobject ):
    def __init__ ( self, size: float = 1, **kwargs ):
        super().__init__ ( 
            DIR/"assets/image/note-block.png",
            **kwargs 
        )
        self._size = size
        self.height = 2 * size
    
    @property
    def size ( self ) -> float:
        return self._size
    
    def animatePlay ( self ):
        mob_note = ImageMobject ( DIR/"assets/image/note-block_note.png" )
        mob_note.height = self.size * 0.5
        mob_note.move_to ( self.get_center ( ) + UP * self.size * 0.5 )
        return AnimationGroup (
            mob_note.animate ( run_time = 1, rate_func = linear )\
                .shift ( UP * self.size * 2 ).fade ( 1 ),
            Wiggle ( self, run_time = 0.5, rate_func = linear ),
        )