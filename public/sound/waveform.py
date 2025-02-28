from collections.abc import Iterable, Sequence, Callable
from typing import Self, TypeVar
from abc import ABCMeta, abstractmethod
import os
from pathlib import Path
import itertools as it

import numpy as np
from scipy.io import wavfile
from scipy.integrate import quad
from sklearn.cluster import DBSCAN

from ..utils.number_theory_utils import approxGCD
from .envelope import Envelope, NoEnvelope

__all__ = [
    "Waveform", 
    "SineWave", 
    "SquareWave",
    "SawtoothWave",
    "TriangleWave", 
    "HarmonicSeries", 
    "analyzeSoundFile",
    "saveSoundFile",
]

PI = np.pi
TAU = 2 * PI
PI_SQR = PI * PI
SQRT2 = np.sqrt ( 2 )
SQRT2_HALF = SQRT2 / 2
SQRT6 = np.sqrt ( 6 )
SQRT6_HALF = SQRT6 / 2

T = TypeVar ( "T", bound = np.dtype )

_debug = True
if _debug and __name__ == "__main__":
    from matplotlib import pyplot as plt

def _addArrays ( 
        arr1: np.ndarray [ T ], arr2: np.ndarray [ T ] 
) -> np.ndarray [ T ]:
    len1, len2 = len ( arr1 ), len ( arr2 )
    minLen, maxLen = min ( len1, len2 ), max ( len1, len2 )
    result = np.empty ( 
        maxLen, dtype = arr1.dtype if len1 > len2 else arr2.dtype
    )
    result [ :minLen ] = arr1 [ :minLen ] + arr2 [ :minLen ]
    if len1 > len2: result [ minLen: ] = arr1 [ minLen: ]
    else: result [ minLen: ] = arr2 [ minLen: ]
    
    return result

@np.vectorize ( excluded = ( 0, ) )
def _fourierCoefByIntegral ( fn: Callable [ [ float ], complex ], n: int ) -> complex:
    """
    Calculate the Fourier coefficient of the waveform at the given index.
    The fourier coefficient is defined by the formula:
    $$ \\hat{f}(k) = \\int_{0}^{1} f(t) \\text{e}^{-2 \\pi ikt} \\text{d}t $$
    """
    return quad ( 
        lambda t: fn ( t ) * np.exp ( -1j * TAU * n * t ), 
        0, 1, complex_func = True 
    ) [ 0 ]

@np.vectorize ( excluded = ( 0, "maxIter", "eps" ) )
def _Waveform_calcStandingWave ( 
        self, x: float, t: float, /, 
        nTerms = 100, eps = 1e-10,
) -> float:
    result = 0
    for k in range ( 1, nTerms + 1 ):
        term = self.calcStandingWaveComponent ( k, x, t )
        result += term
        if np.fabs ( term ) < eps: break
    # else:
    #     warnings.warn ( 
    #         f"Max iteration reached for standing wave at {x = }, {t = }." 
    #     )
    return result

class Waveform ( metaclass = ABCMeta ):
    @abstractmethod
    def calc ( self, t: float ) -> complex:
        raise NotImplementedError
    
    def calcHarmonic ( self, k: int, t: float ) -> complex:
        return self._fourierCoef ( k ) * np.exp ( 1j * TAU * k * t )
    
    def calcStandingWaveComponent ( self, k: int, x: float, t: float ) -> float:
        return self.calcHarmonic ( k, t ).imag * np.sin ( PI * k * x )
    
    def calcStandingWave ( 
        self, x: float, t: float, /, 
        nTerms = 100,
    ) -> float:
        return _Waveform_calcStandingWave ( self, x, t, nTerms = nTerms )
    
    def __call__ ( self, t: float ) -> float:
        return self.calc ( t ).imag
    
    def _fourierCoef ( self, n: int ) -> complex:
        # print ( "_fourierCoef from Waveform called" )
        return _fourierCoefByIntegral ( lambda t: self.calc ( t ), n )
    
    def _slice ( self, n: slice ) -> "Waveform":
        if n.stop is None:
            start, step = n.start, n.step
            if step is None: step = 1
            elif step < 0: step = -step
            if start is None: start = step - 1
            return self._infiniteSlice ( start, step )
        if n.step is not None and n.step < 0:
            n = slice ( n.start, n.stop, -n.step )
        start, stop, step = n.indices ( n.stop )
        if n.start is None: start = step - 1
        data = np.empty ( stop, dtype = complex )
        data [ start : stop : step ] = self._fourierCoef ( 
            np.arange ( start, stop, step ) + 1 
        )
        return HarmonicSeries._newFromTrustedArray ( data )

    def _infiniteSlice ( self, start: int, step: int ) -> "Waveform":
        raise ValueError ( "Slice stop cannot be None for a general waveform" )
    
    def __getitem__ ( self, n: int | slice ) -> "complex | Waveform":
        if isinstance ( n, slice ): return self._slice ( n )
        else: return self._fourierCoef ( n )

class BasicWaveform ( Waveform, metaclass = ABCMeta ):
    def __repr__ ( self ):
        return f"{self.__class__.__name__}()"

class EmptyWave ( BasicWaveform ):
    _instance = None
    
    def __new__ ( cls ):
        if cls._instance is None:
            cls._instance = super ( ).__new__ ( cls )
        return cls._instance
    
    def calc ( self, t: float ) -> complex:
        return 0
    
    def __call__ ( self, t: float ) -> float:
        return 0
    
    def _fourierCoef ( self, n: int ) -> complex:
        return 0
    
    def _slice ( self, n: slice ) -> Self:
        return self

@np.vectorize
def _sineWaveFourierCoef ( n: int ) -> complex:
    if n == 1: return 1
    else: return 0

class SineWave ( BasicWaveform ):
    _instance = None
    
    def __new__ ( cls ):
        if cls._instance is None:
            cls._instance = super ( ).__new__ ( cls )
        return cls._instance
    
    def calc ( self, t ):
        return np.exp ( 1j * TAU * t )
    
    def _fourierCoef ( self, n: int ) -> complex:
        return _sineWaveFourierCoef ( n )
    
    def _infiniteSlice ( self, start: int, step: int ) -> "Self | EmptyWave":
        if start > 0: return EmptyWave ( )
        else: return self

def _squareWaveReal ( t: float ) -> float:
    return -SQRT2 * np.log ( np.abs ( np.tan ( PI * t ) ) ) / PI

@np.vectorize
def _squareWaveImag ( t: float ) -> float:
    t %= 1
    # if t == 0: return 0
    if t < 0.5: return SQRT2_HALF
    else: return -SQRT2_HALF

@np.vectorize
def _squareWaveFourierCoef ( k: int ) -> complex:
    if k <= 0 or k % 2 == 0: return 0
    else: return 2 * SQRT2 / k / PI

class SquareWave ( BasicWaveform ):
    _instance = None
    
    def __new__ ( cls ):
        if cls._instance is None:
            cls._instance = super ( ).__new__ ( cls )
        return cls._instance
    
    def calc ( self, t: float ) -> complex:
        return complex ( _squareWaveReal ( t ), _squareWaveImag ( t ) )
    
    def __call__ ( self, t: float ) -> float:
        return _squareWaveImag ( t )
    
    def _fourierCoef ( self, k: int ) -> complex:
        return _squareWaveFourierCoef ( k )

def _sawtoothWaveReal ( t: float ) -> float:
    return -SQRT6 * np.log ( 2 * np.abs ( np.sin ( PI * t ) ) ) / PI

def _sawtoothWaveImag ( t: float ) -> float:
    return SQRT6_HALF - SQRT6 * ( t % 1 )

@np.vectorize
def _sawtoothWaveFourierCoef ( k: int ) -> complex:
    if k <= 0: return 0
    else: return SQRT6 / k / PI

class SawtoothWave ( BasicWaveform ):
    _instance = None
    
    def __new__ ( cls ):
        if cls._instance is None:
            cls._instance = super ( ).__new__ ( cls )
        return cls._instance
    
    def calc ( self, t: float ) -> complex:
        result = complex ( _sawtoothWaveReal ( t ), _sawtoothWaveImag ( t ) )
        # print ( result )
        return result
    
    def __call__ ( self, t: float ) -> float:
        return _sawtoothWaveImag ( t )
    
    def _fourierCoef ( self, k: int ) -> complex:
        return _sawtoothWaveFourierCoef ( k )

@np.vectorize
def _triangleWaveReal ( t: float ) -> float:
    t *= 1
    result = 0
    for i in it.count ( 1 ):
        k = 2 * i - 1
        term = np.cos ( 2 * k * PI * t ) / k / k
        if i % 2 == 0: result -= term
        else: result += term
        if np.fabs ( term ) < 1e-10: break
    return result * 4 * SQRT6 / PI_SQR

@np.vectorize
def _triangleWaveImag ( t: float ) -> float:
    t %= 1
    if t < 0.25: return 2 * SQRT6 * t
    if t < 0.75: return ( 1 - 2 * t ) * SQRT6
    else: return 2 * SQRT6 * ( t - 1 )

@np.vectorize
def _triangleWaveFourierCoef ( k: int ) -> complex:
    if k <= 0 or k % 2 == 0: return 0
    else: 
        result = 4 * SQRT6 / k / k / PI_SQR
        if k % 4 != 1: result = -result
        return result

class TriangleWave ( BasicWaveform ):
    _instance = None
    
    def __new__ ( cls ):
        if cls._instance is None:
            cls._instance = super ( ).__new__ ( cls )
        return cls._instance
    
    def calc ( self, t: float ) -> complex:
        return complex ( _triangleWaveReal ( t ), _triangleWaveImag ( t ) )
    
    def __call__ ( self, t: float ) -> float:
        return _triangleWaveImag ( t )
    
    def _fourierCoef ( self, k: int ) -> complex:
        return _triangleWaveFourierCoef ( k )

def _normalizeData ( data: np.ndarray [ complex ] ) -> np.ndarray [ complex ]:
    phi0 = np.angle ( data [ 0 ] )
    data /= np.exp ( 1j * phi0 )
    data /= np.linalg.norm ( data )
    return data

@np.vectorize ( excluded = ( 0, ) )
def _calcHarmonics ( data: np.ndarray [ complex ], t: float ) -> np.ndarray [ complex ]:
    return np.exp ( 
        1j * TAU * t * 
        ( np.arange ( len ( data ) ) + 1 )
    ) * data

@np.vectorize ( excluded = ( 0, ) )
def _harmonicSeries_calc ( data: np.ndarray [ complex ], t: float ) -> complex:
    return np.sum ( _calcHarmonics ( data, t ) )

@np.vectorize ( excluded = ( 0, ) )
def _calcStandingWaveComponents ( data, x: float, t: float ) -> np.ndarray [ float ]:
    return ( 
        _calcHarmonics ( data, t ).imag * 
        np.sin ( PI * x * np.arange ( 1, len ( data ) + 1 ) )
    )

@np.vectorize ( excluded = ( 0, ) )
def _HarmonicSeries_calcStandingWave ( 
        data: np.ndarray [ complex ], 
        x: float, t: float,
) -> float:
    return np.sum ( _calcStandingWaveComponents ( data, x, t ) )

@np.vectorize ( excluded = ( 0, ) )
def _HarmonicSeries_fourierCoef ( data: np.ndarray [ complex ], n: int ) -> complex:
    # print ( "_fourierCoef from HarmonicSeries called" )
    if n <= 0 or n > len ( data ): return 0
    return data [ n - 1 ]

@np.vectorize ( excluded = ( 0, ) )
def _HarmonicSeries_calcHarmonic ( data: np.ndarray [ complex ], k: int, t: float ) -> complex:
    if k <= 0 or k > len ( data ): return 0
    return np.exp ( 1j * TAU * k * t ) * data [ k - 1 ]

class HarmonicSeries ( Waveform, Sequence [ complex ] ):
    @classmethod
    def fromAmpAndPhase ( 
        cls, amps: Iterable [ float ], 
        phases: Iterable [ float ] 
    ) -> Self:
        amps = np.array ( amps, dtype = float )
        phases = np.array ( phases, dtype = float )
        amps /= np.linalg.norm ( amps )
        phases -= phases [ 0 ]
        data = amps * np.exp ( 1j * phases )
        return cls._newWFromTrustedArray ( data, False )
    
    def __new__ ( cls, *data: complex ):
        return cls._newFromTrustedArray ( 
            np.array ( data, dtype = complex ) 
        )
    
    @classmethod
    def _newWithoutNormalize ( cls, *data: complex ) -> Self:
        return cls._newFromTrustedArray ( 
            np.array ( data, dtype = complex ),
            False
        )
    
    @classmethod
    def _newFromTrustedArray ( 
            cls, data: np.ndarray [ complex ], 
            normalize: bool = True 
    ) -> Self:
        self = super ( ).__new__ ( cls )
        self._data = data
        if normalize: _normalizeData ( self._data )
        self._data.flags.writeable = False
            
        return self
    
    def calcHarmonic ( self, k: int, t: float ) -> complex:
        return _HarmonicSeries_calcHarmonic ( self._data, k, t )
    
    def calcHarmonics ( self, t: float ) -> np.ndarray [ complex ]:
        return _calcHarmonics ( self._data, t )
    
    def calc ( self, t: float ) -> complex:
        return _harmonicSeries_calc ( self._data, t )
    
    def calcStandingWaveComponents ( self, x: float, t: float ) -> np.ndarray [ float ]:
        return _calcStandingWaveComponents ( self._data, x, t )
    
    def calcStandingWave ( self, x: float, t: float ) -> float:
        return _HarmonicSeries_calcStandingWave ( self._data, x, t )
    
    def _fourierCoef ( self, n: int ) -> complex:
        return _HarmonicSeries_fourierCoef ( self._data, n )
    
    def _slice ( self, n: slice ) -> Self:
        if n.step is not None and n.step < 0:
            # negative step will be converted to its absolute value
            n = slice ( n.start, n.stop, -n.step )
        start, stop, step = n.indices ( len ( self._data ) )
        if n.start is None: start = step - 1
        newData = np.zeros ( stop, dtype = complex )
        newData [ start : stop : step ] = self._data [ start : stop : step ]
        return self._newFromTrustedArray ( newData )
    
    def __len__ ( self ):
        return len ( self._data )
    
    def __iter__ ( self ):
        return iter ( self._data )
    
    def __repr__ ( self ):
        return f"{self.__class__.__name__}(\n{self._data}\n)"
    
    @property
    def data ( self ): return self._data
    
    def __or__ ( self, n: int ) -> Self:
        return self.__class__ ( *self._data [ n - 1 :: n ] )
    
    def __add__ ( self, other: Self ) -> Self:
        return self._newFromTrustedArray ( *_addArrays ( self._data, other._data ) )
    
    def __sub__ ( self, other: Self ) -> Self:
        return self._newFromTrustedArray ( *_addArrays ( self._data, -other._data ) )
    
    def __neg__ ( self ):
        return self._newFromTrustedArray ( -self._data, False )
    
    def __mul__ ( self, n: int ) -> Self:
        newData = np.zeroes ( len ( self._data ) * n, dtype = complex )
        newData [ n - 1 :: n ] = self._data
        return self._newFromTrustedArray ( newData, False )

def analyzeSoundFile ( 
    path: os.PathLike, /,
    sampleTime: float | None = None,
    channel: int = 0,
    freqTolerance: float = 100,
    harmonicThreshold: float = 0.1,
) -> tuple [ float, HarmonicSeries ]:
    path = Path ( path )
    sampleRate, audioData = wavfile.read ( path )
    totalTime = len ( audioData ) / sampleRate
    
    if sampleTime is None:
        sampleTime = totalTime
    else:
        nSamples = int ( sampleRate * sampleTime )
        audioData = audioData [ :nSamples ]
    
    if len ( audioData.shape ) == 2:
        # stereo
        nChannels = audioData.shape [ 1 ]
        channel = min ( channel, nChannels - 1 )
        audioData = audioData [ :, channel ]
    
    fftResult = np.fft.fft ( audioData )
    fftResult = fftResult [ : len ( fftResult ) // 2 ]
    fftAmps = np.abs ( fftResult )
    maxAmp = np.max ( fftAmps )
    
    peaks = np.where ( fftAmps > maxAmp * harmonicThreshold ) [ 0 ]
    clusterResult = DBSCAN ( 
        eps = freqTolerance * sampleTime, 
        min_samples = 1 
    ).fit ( peaks.reshape ( -1, 1 ) )
    labels = clusterResult.labels_
    nClusters = np.max ( labels ) + 1
    
    centers = np.empty ( nClusters, dtype = int )
    for k in range ( nClusters ):
        cluster = peaks [ labels == k ]
        centers [ k ] = cluster [ np.argmax ( fftAmps [ cluster ] ) ]
        # print ( fftAmps [ cluster ] / maxAmp, np.argmax ( fftAmps [ cluster ] ) )
    baseFreqIdx = approxGCD ( centers, freqTolerance )
    
    # print ( peaks )
    # print ( centers )
    
    nHarmonics = round ( centers [ -1 ] / baseFreqIdx )
    result = np.zeros ( nHarmonics, dtype = complex )
    for center in centers:
        k = round ( center / baseFreqIdx )
        # print ( center, baseFreqIdx, i )
        result [ k - 1 ] = fftResult [ center ]

    phi0 = np.angle ( result [ 0 ] )
    result /= np.sqrt ( np.sum ( np.abs ( result ) ** 2 ) )
    result /= np.exp ( 1j * phi0 )
    
    ############ start plotting code
    
    if _debug and __name__ == "__main__":
        plt.figure ( figsize = ( 12, 3 ) )
        plt.subplot ( 1, 3, 1 )
        normalizedFftAmps = fftAmps / maxAmp
        nSamples = len ( audioData ) // 2
        plt.xlim ( 20, 20000 )
        plt.xscale ( "log" )
        plt.yscale ( "log" )
        freqX = np.arange ( nSamples ) / sampleTime
        plt.plot ( 
            freqX, normalizedFftAmps,
            color = "#dd6236",
            linewidth = 0.75,
        )
        plt.fill_between ( 
            freqX, normalizedFftAmps,
            color = "#dd623680"
        )
        plt.scatter ( 
            peaks / sampleTime, 
            normalizedFftAmps [ peaks ], 
            marker = ".", 
            color = "black",
        )
        plt.axhline ( 
            y = harmonicThreshold, 
            color = "black", 
            linewidth = 0.5 
        )
    
    ############ end plotting code
        
    return (
        baseFreqIdx / sampleTime, 
        HarmonicSeries._newWithoutNormalize ( *result )
    )

def saveSoundFile ( 
    waveform: Waveform,  
    path: os.PathLike,
    freq: float = 440, 
    duration: float = 2, 
    volume: float = 0.5,
    envelope: Envelope = NoEnvelope ( ), 
    sampleRate: int = 44100, 
    phaseShift: float = 0,
    prependTime: float = 0.2,
) -> None:
    t = np.linspace ( 0, duration, int ( sampleRate * duration ), endpoint = False )
    audioData = np.int16 ( 
        envelope.calc ( t, duration ) * 
        waveform ( t * freq - phaseShift ) * 
        volume * 32767
    )
    wavfile.write ( 
        path, sampleRate, 
        np.concat ((
            np.zeros ( 
                int ( sampleRate * prependTime ),
                dtype = np.int16,
            ), 
            audioData 
        ))
    )

if __name__ == "__main__":
    from envelope import ADSR, Fading
    DIR = Path ( __file__ ).parent if "__file__" in locals ( ) else Path.cwd ( )
    
    # Basic Waveforms Example
    basicWaveforms = (
        SineWave ( ),
        SquareWave ( ),
        SawtoothWave ( ),
        TriangleWave ( ),
    )
    print ( basicWaveforms )
    basicWaveformNames = ( "sine", "square", "sawtooth", "triangle" )
    
    if _debug:
        plt.figure ( figsize = ( 12, 6 ) )
        for i, waveform in enumerate ( basicWaveforms ):
            cutoffWaveform = waveform [ :10 ]
            plt.subplot ( 2, 2, i + 1 )
            x = np.linspace ( 0, 1, 1000 )
            plt.plot ( x, waveform ( x ), color = "#006400" )
            plt.plot ( x, cutoffWaveform ( x ), color = "#00640080" )
            plt.axhline ( y = 0, color = "black", linewidth = 0.5 )
        plt.tight_layout ( )
    
    for name, waveform in zip ( basicWaveformNames, basicWaveforms ):
        saveSoundFile ( waveform, DIR/f"output/{name}.wav" )
    
    # Harmonic Series Example
    
    analyzeConfig = {
        "freqTolerance": 100,
        "sampleTime": 0.5,
        "harmonicThreshold": 0.05,
    }
    instruments = ( "piano", "violin", "oboe", "trombone" )
    envelopes = (
        ADSR ( 
            0, 2, 0, 0,
            decayEasing = lambda x: x**5
        ),
        Fading ( 0.5, 0.5 ),
        Fading ( 1, 0.5 ),
        Fading ( 0.5, 1 ),
    )
    
    for instrument, envelope in zip ( instruments, envelopes ):
        baseFreq, result = analyzeSoundFile ( 
            DIR/f"assets/sound/{instrument}.wav",
            **analyzeConfig
        )
        print ( baseFreq )
        print ( result )
        
        if _debug:
            plt.subplot ( 1, 3, 2 )
            bars = plt.bar ( 
                range ( 1, len ( result.data ) + 1 ), 
                np.abs ( result.data ),
                color = "#d32f2f80"
            )
            for bar in bars: 
                bar.set_edgecolor ( "#d32f2f" )
                bar.set_linewidth ( 0.5 )
            
            plt.subplot ( 1, 3, 3 )
            x = np.linspace ( 0, 1, 100 )
            plt.axhline ( 
                y = 0, 
                color = "black", 
                linewidth = 0.5 
            )
            plt.plot ( 
                x, result ( x ),
                color = "#006400",
            )
            
            plt.tight_layout ( )
        
        saveSoundFile ( 
            result,
            DIR/f"output/{instrument}_synthed.wav",
            envelope = envelope,
        )
    
    if _debug:
        plt.show ( )













