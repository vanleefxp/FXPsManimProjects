from fractions import Fraction as Q

__all__ = [
    "frac2Latex",
]

def frac2Latex ( frac: Q ) -> str:
    n, d = frac.numerator, frac.denominator
    if d == 1: return str ( n )
    elif n > 0: return f"\\frac{{{ n }}}{{{ d }}}"
    else: return f"-\\frac{{{ -n }}}{{{ d }}}"