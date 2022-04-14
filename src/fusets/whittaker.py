import math
from datetime import timedelta

import numpy as np
from vam.whittaker import ws2d


def whittaker_f(x, y, lmbd, d):
    # minimum and maximum dates
    min = x[0].toordinal()
    max = x[-1].toordinal()
    l = max - min

    v = np.full(l + 1, -3000)
    t = np.full(l + 1, 0, dtype='float')

    D = []
    for i in x:
        D.append(i.toordinal())

    D1 = np.array(D) - D[0]
    D11 = D1[~np.isnan(y)]
    v[D11] = 1
    t[D11] = y[~np.isnan(y)]

    # dates
    xx = [x[0] + timedelta(days=i) for i in range(l + 1)]  # try using pandas instead?

    # create weights
    w = np.array((v != -3000) * 1, dtype='double')

    # apply filter
    z_ = ws2d(t, lmbd, w)
    z1_ = np.array(z_)

    # return z1_,xx

    if isinstance(d, int):
        if d > 0 and d < z1_.size:
            n = z1_.size
            ind = [i * d for i in range(math.ceil(n / d))]
            Zd = z1_[ind]
            XXd = [xx[ii] for ii in ind]
        else:
            Zd = []
            XXd = []
            print("d must be positive and smaller than the total number of dates")
    else:
        Zd = []
        XXd = []
        print("d must be an integer")

    return z1_, xx, Zd, XXd
