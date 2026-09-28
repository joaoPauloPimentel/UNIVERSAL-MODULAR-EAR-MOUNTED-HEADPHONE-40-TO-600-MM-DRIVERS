import math
import numpy as np


def js(o):
    """JSON-safe conversion (numpy -> python, inf/nan -> strings)."""
    if isinstance(o, dict):
        return {str(k): js(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [js(v) for v in o]
    if isinstance(o, np.ndarray):
        return js(o.tolist())
    if isinstance(o, np.floating):
        o = float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, complex):
        return [o.real, o.imag]
    if isinstance(o, float) and (math.isinf(o) or math.isnan(o)):
        return str(o)
    return o
