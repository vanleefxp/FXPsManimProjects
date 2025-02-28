import sys
from pathlib import Path

import numpy as np

DIR = Path ( __file__ ).parent if "__file__" in locals ( ) else Path.cwd ( )
sys.path.append ( str ( ( DIR/".." ).resolve ( ) ) )
from public import *

if __name__ == "__main__":
    # Example 1
    data = np.array ( ( 500, 600, 700, 800, 900 ), dtype = float )
    data += np.random.uniform ( -2, 2, size = len ( data ) )
    np.random.shuffle ( data )
    print ( data )
    print ( approxGCD ( data, 50 ) )
    
    # Example 2
    data = np.array ( ( 3, 6, 15, 21, 24, 30 ), dtype = float )
    data += np.random.uniform ( -0.01, 0.01, size = len ( data ) )
    np.random.shuffle ( data )
    print ( data )
    print ( approxGCD ( data, 1 ) ) 
    