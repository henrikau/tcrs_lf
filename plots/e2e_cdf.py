#!/usr/bin/env python3
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import statistics
import numpy as np

# path=os.path.abspath(os.path.dirname(sys.argv[0]))
# sys.path.append('{}/net_chan/plots'.format(os.path.dirname(os.path.dirname(path))))
from lib import *
import lib.timedc_lib as tc


SMALL_SIZE = 12
MEDIUM_SIZE = 17
BIGGER_SIZE = 24

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=MEDIUM_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
plt.rc('figure', titlesize=50)  # fontsize of the figure title

def read_e2e(fname):
    df = pd.read_csv("../tcrs_dataset/{}".format(fname))
    df['date'] = pd.to_datetime(df['t1'],unit='ns')
    df['diff_ns'] = df['t2'] - df['t1']
    df['diff_us'] = df['diff_ns']/1e3
    df['diff_ms'] = df['diff_ns']/1e6
    return df

def plot_pdf_cdf(df, ax, title, xlim=None):
    # Find cdf of each e2e delay and overlay in plot
    # Find histogram for each diff_ns
    # 1. Histogram to get buckets and frequency
    # 2. Plot histo
    # 3. sum and create cdf

    # diff_ms = np.array(df['diff_ns']/1e6)
    diff_ms = np.array(df['diff_ms'])
    N = len(diff_ms)
    hist, bin_edges = np.histogram(diff_ms, bins=750)
    hist = hist/N
    cdf = [hist[0]]
    maxidx = np.array(hist).argmax()

    print("{}".format(title))
    print("Min: {:.3f} $\mu$s &".format(min(df['diff_us'])))
    print("Max: {:.3f} $\mu$s &".format(max(df['diff_us'])))
    print("Avg: {:.3f} $\mu$s &".format(statistics.mean(df['diff_us'])))
    print("Stdev: {:.3f} $\mu$s & ".format(statistics.stdev(df['diff_us'])))
    print("Peak: idx={:<5d} count={:<6d} {:.3f} $\mu$s".format(maxidx, int(hist[maxidx]*N), 1000*(bin_edges[maxidx]+ bin_edges[maxidx+1]) / 2))
    print("")


    for i in range(1, len(hist)):
        cdf.append(cdf[i-1] + hist[i])

    ax2 = ax.twinx()
    ax.plot(bin_edges[1:], hist, color='blue', label='PDF')
    ax2.plot(bin_edges[1:], cdf, color='red', label='CDF')
    if xlim:
        ax.set_xlim(xlim)
    else:
        ax.set_xlim((bin_edges[0], bin_edges[-1]))
    ax.set_ylim((0, 1.05*max(hist)))
    ax2.set_ylim((0, 1.05))

    ax.set_title(title)

    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc=0)


if __name__ == "__main__":
    df_fi = read_e2e('federated_e2e_idle.csv')
    df_fi = df_fi.drop([0]) # first value contained error (outlier)
    df_fn = read_e2e('federated_e2e_noise.csv')
    df_nci = read_e2e('netchan_e2e_idle.csv')
    df_ncn = read_e2e('netchan_e2e_noise.csv')


    fig = plt.figure(num=None, figsize=(20, 12),
                     dpi=150,
                     facecolor='w', edgecolor='k')
    plt.tight_layout()
    plot_pdf_cdf(df_fi,  fig.add_subplot(221), "Federated E2E (idle)")
    plot_pdf_cdf(df_nci, fig.add_subplot(222), "NetChan E2E (idle)", xlim = (2.012, 2.045))
    plot_pdf_cdf(df_fn,  fig.add_subplot(223), "Federated E2E (noise)")
    ax = fig.add_subplot(224)
    plot_pdf_cdf(df_ncn, ax, "NetChan E2E (noise)", xlim = (2.012, 2.043))
    ax.set_xlabel("Delay (ms)")
    fig.savefig("tcrs_e2e_cdf.png", bbox_inches='tight')
    # plt.show()
