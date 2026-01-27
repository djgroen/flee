def interp(a, i):
    if i < 0 or i >= len(a) - 1:
        raise IndexError("Index out of interpolation range")
    i0 = int(i)
    frac = i - i0
    return a[i0] + frac * (a[i0 + 1] - a[i0])
