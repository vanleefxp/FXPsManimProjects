# from manim import *
import numpy as np

def cropLine ( 
    line: np.ndarray, # shape: (2, d)
    bounds: np.ndarray, # shape: (d, 2)
) -> np.ndarray:
    d = line.shape [ 1 ] # dimension
    p1, p2 = line # endpoints of the line
    vec = p2 - p1 # direction vector of the line
    positions = [ ]
    for i in range ( d ): 
        xi_min, xi_max = bounds [ i ] # range of the i-th coordinate of the line
        xi1, xi2 = p1 [ i ], p2 [ i ] # i-th coordinates of the endpoints
        dxi = xi2 - xi1
        positions.append ( ( xi_min - xi1 ) / dxi )
        positions.append ( ( xi_max - xi1 ) / dxi )
    return np.array ( positions )


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    n = 1
    bounds = np.array (( ( -1, 1 ), ( -1, 1 ) ))
    points = np.random.uniform ( -3.0, 3.0, size = ( n, 2, 2 ) )
    plt.plot ( ( -1, 1, 1, -1, -1 ), ( -1, -1, 1, 1, -1 ), color = "black" )
    plt.gca ( ).set_aspect ( "equal" )
    for pointPair in points:
        print ( pointPair )
        plt.plot ( *pointPair.T, color = "black", linewidth = 0.5 )
        cropPoints = cropLine ( pointPair, bounds )
        p1, p2 = pointPair
        for t in cropPoints:
            p = p1 + t * ( p2 - p1 )
            plt.scatter ( *p, marker = "x", color = "red" )
        print ( cropPoints )
    plt.show ( )