from collections.abc import Iterable, Callable
from pathlib import Path
import subprocess, shutil, time
from numbers import Integral

from manim import *
from music21.stream import Stream as MidiStream
from music21.note import Note
from music21.chord import Chord
from music21.tempo import MetronomeMark
import toml

__all__ = [ "generateNoteMidi", "generateChordMidi", "addMidi" ]

DIR = Path ( __file__ ).parent if "__file__" in locals ( ) else Path.cwd ( )
_bpm60 = MetronomeMark ( number = 60 )
_soundfontConfig = toml.load ( DIR/"assets/soundfont.toml" )
_soundfontPath = Path ( _soundfontConfig [ "soundfontPath" ] )

def generateNoteMidi ( 
        noteValue: int,
        length: float = 1,
) -> MidiStream:
    melody = MidiStream ( )
    melody.append ( _bpm60 )
    n = Note ( noteValue )
    n.quarterLength = length
    melody.append ( n )
    return melody

def generateChordMidi (
    noteValues: Iterable [ int ],
    length: float = 1,
) -> MidiStream:
    melody = MidiStream ( )
    melody.append ( _bpm60 )
    c = Chord ( tuple ( noteValues ) )
    c.quarterLength = length
    melody.append ( c )
    return melody

def midi2wav ( 
        midiStream: MidiStream,
        sampleRate: int = 44100,
        gain: float = 2,
) -> tuple [ Path, Callable [ [ ], None ] ]:
    tempFolder = DIR/"_tmp"
    tempFolder.mkdir ( exist_ok = True )
    filename = f"temp_{time.monotonic_ns ( )}"
    midiPath = tempFolder/f"{filename}.mid"
    midiStream.write ( "midi", midiPath )
    wavPath = tempFolder/f"{filename}.wav"
    subprocess.run ( (
        "fluidsynth", "-ni", 
        "-g", str ( gain ), 
        str ( _soundfontPath ), 
        str ( midiPath ), 
        "-F", str ( wavPath ), 
        "-r", str ( sampleRate ),
    ) )
    if not wavPath.exists ( ):
        raise Exception ( 
            f"Failed to generate WAV file from MIDI file: {midiPath}." 
            "Please check if `fluidsynth` is correctly installed and "
            "if the soundfont file is valid."
        )
    wavPath = wavPath.resolve ( )
    def _dispose ( ):
        if tempFolder.exists ( ):
            shutil.rmtree ( tempFolder )
    return wavPath, _dispose

def addMidi ( 
    scene: Scene, 
    midi: MidiStream | int | Iterable [ int ], 
    timeOffset: float = 0,
    gain: float = 2,
):
    if isinstance ( midi, Integral ):
        midi = generateNoteMidi ( midi )
    elif not isinstance ( midi, MidiStream ):
        midi = generateChordMidi ( midi )
    wavPath, dispose = midi2wav ( midi, gain = gain )
    scene.add_sound ( wavPath, time_offset = timeOffset )
    dispose ( )

