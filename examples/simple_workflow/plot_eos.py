#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-

import numpy as np
from matplotlib import pyplot as plt
import sys


def birch_murnaghan(V, E0, V0, B0, B01):
    r = (V0 / V) ** (2. / 3.)
    return E0 + 9. / 16. * B0 * V0 * (r - 1.) ** 2 * \
                (2. + (B01 - 4.) * (r - 1.))


def fit_birch_murnaghan_params(volumes_, energies_):
    from scipy.optimize import curve_fit

    volumes = np.array(volumes_)
    energies = np.array(energies_)
    params, covariance = curve_fit(
        birch_murnaghan, xdata=volumes, ydata=energies,
        p0=(
            energies.min(),  # E0
            volumes.mean(),  # V0
            0.1,  # B0
            3.,  # B01
        ),
        sigma=None
    )
    return params, covariance


def plot_eos(eos_pk):
    """
    Plots equation of state taking as input the pk of the ProcessCalculation 
    printed at the beginning of the execution of run_eos_wf 
    """
    # from matplotlib import pylab as pl
    from aiida.orm import load_node
    eos_calc=load_node(eos_pk)
    eos_result=eos_calc.out.result
    raw_data = eos_result.dict.eos_data
    
    data = []
    for V, E, units in raw_data:
        data.append((V,E))
      
    data = np.array(data)
    params, covariance = fit_birch_murnaghan_params(data[:,0],data[:,1])
    
    vmin = data[:,0].min()
    vmax = data[:,0].max()
    vrange = np.linspace(vmin, vmax, 300)

    plt.plot(data[:,0],data[:,1],'o')
    plt.plot(vrange, birch_murnaghan(vrange, *params))

    plt.xlabel("Volume (ang^3)")
    # I take the last value in the list of units assuming units do not change
    plt.ylabel("Energy ({})".format(units))
    plt.show()


    # data = []
    # for E, units in raw_data:
        # data.append(E)
    # data = np.array(data)
    # plt.plot(data,'o')
    # plt.show()


if __name__=="__main__":
    plot_eos(sys.argv[1])
