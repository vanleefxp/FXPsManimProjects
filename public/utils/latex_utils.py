from numbers import Rational

__all__ = [
    "frac2Latex",
]

def frac2Latex ( 
    frac: Rational, 
    slant: bool = False, 
    show1: bool = False,
    small: bool = False,
) -> str:
    n, d = frac.numerator, frac.denominator
    if d == 1 and not show1: return str ( n )
    elif slant: return f"{n}/{d}"
    else:
        prefix = "tfrac" if small else "frac"
        if n > 0: return f"\\{ prefix }{{{ n }}}{{{ d }}}"
        else: return f"-\\{prefix}{{{ -n }}}{{{ d }}}"