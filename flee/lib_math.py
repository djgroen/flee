def interp(a, i):
    # a: python list
    # i: index value to be interpolated (float).
    if i < 0 or i >= len(a) - 1:
        raise IndexError("interp failed: Index out of interpolation range")
    i0 = int(i)
    frac = i - i0
    return a[i0] + frac * (a[i0 + 1] - a[i0])

def dict_interp(data, key, index_col, index_val):
    # d: dict to look into.
    # k: key containing values to be interpolated.
    # index_col: key of (time) value col, so support interpolation.
    indices = data[index_col]
    values = data[key]

    if index_val < indices[0] or index_val > indices[-1]:
        raise ValueError("dict_interp failed: Index_val outside interpolation range of dict_interp.")

    for i in range(len(indices) - 1):
        if indices[i] <= index_val <= indices[i + 1]:
            x0, x1 = indices[i], indices[i + 1]
            y0, y1 = values[i], values[i + 1]
            return y0 + (y1 - y0) * (index_val - x0) / (x1 - x0)

    raise RuntimeError("dict_interp failed: Interpolation failed due to input in invalid format.")
