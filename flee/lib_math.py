import sys
import math


def interp(a: list, i: float) -> float:
    # a: python list
    # i: index value to be interpolated (float).
    if i < 0 or i >= len(a) - 1:
        raise IndexError("interp failed: Index out of interpolation range")
    i0 = int(i)
    frac = i - i0
    return a[i0] + frac * (a[i0 + 1] - a[i0])


def dict_interp(data, key, index_col, index_val) -> float:
    # d: dict to look into.
    # k: key containing values to be interpolated.
    # index_col: key of (time) value col, so support interpolation.
    try:
        indices = data[index_col]
    except KeyError:
        print(f"KeyError in dict_interp for column {index_col}", file=sys.stderr)
        print(f"{data}", file=sys.stderr)
        raise KeyError

    values = data[key]

    if index_val < indices[0] or index_val > indices[-1]:
        raise ValueError(f"dict_interp failed: Index_val {index_val} outside interpolation range of dict_interp {indices}.")

    for i in range(len(indices) - 1):
        if indices[i] <= index_val <= indices[i + 1]:
            x0, x1 = indices[i], indices[i + 1]
            y0, y1 = values[i], values[i + 1]
            return y0 + (y1 - y0) * (index_val - x0) / (x1 - x0)

    raise RuntimeError("dict_interp failed: Interpolation failed due to input in invalid format.")


def calc_loc_dist(location1, location2) -> float:
    """
    Summary: 
        Calculates the distance between this location and another one.
        This assumes distance as the crow flies.

    Args:
        other_location: The other location to calculate the distance to.

    Returns:
        The distance between this location and the other location in kilometers.

    """
    # Approximate radius of earth in km
    R = 6371.0

    lat1 = math.radians(location1.y)
    lon1 = math.radians(location1.x)
    lat2 = math.radians(location2.y)
    lon2 = math.radians(location2.x)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

