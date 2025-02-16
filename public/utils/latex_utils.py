from fractions import Fraction as Q

__all__ = [
    "frac2Latex",
]

def frac2Latex ( frac: Q, slant: bool = False ) -> str:
    n, d = frac.numerator, frac.denominator
    if d == 1: return str ( n )
    elif slant: return f"{n}/{d}"
    elif n > 0: return f"\\frac{{{ n }}}{{{ d }}}"
    else: return f"-\\frac{{{ -n }}}{{{ d }}}"