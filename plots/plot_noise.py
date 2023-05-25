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
import lib.NetNoise as noise


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
    df['t1_rel_ns'] = df['t1'] - df['t1'].iloc[0]
    df['t1_rel_s'] = df['t1_rel_ns']/1e9
    df['diff_ns'] = df['t2'] - df['t1']
    df['diff_us'] = df['diff_ns']/1e3
    df['diff_ms'] = df['diff_ns']/1e6
    return df

def do_plot(ax, df, noise):
    # plot e2e
    ax.plot(df['t1_rel_s'], df['diff_us'], label="E2E delay")


    # Add noise
    ax2 = ax.twinx()
    print(n1.df.iloc[0])
    noise_ts = n1.df['time_rel']
    noise_bw = n1.df['bwmbps']

    ax.plot([-1], [-1], color='red', label="Noise") # hack to get on legend
    ax2.plot(noise_ts, noise_bw, color='red')
    ax2.set_ylim((0, 1100))

    ax.legend(loc='lower right')
    ax.set_ylabel("E2E Delay ($\mu$s)")
    ax.set_xlabel("Relative time (sec)")
    ax.set_xlim((df['t1_rel_s'].iloc[0],  df['t1_rel_s'].iloc[-1]))
    # ax.set_ylim((0, max(df['diff_us'])*1.05))
    ax.set_yscale("log")

if __name__ == "__main__":
    print("hello, world")
    base = "../tcrs_dataset"
    n1 = noise.NetNoise("{}/hercules_noise_federated.log".format(base), "Netnoise, No SRP, 30 sec cycles", 2.8)
    df_fn = read_e2e('federated_e2e_noise.csv')

    n2 = noise.NetNoise("{}/hercules_noise_netchan.log".format(base), "Netnoise, No SRP, 30 sec cycles", 2.8)
    df_ncn = read_e2e('netchan_e2e_noise.csv')

    fig = plt.figure(num=None, figsize=(24,13.5), dpi=160, facecolor='w', edgecolor='k')
    fig.suptitle("E2E delay w/noise overlay")
    plt.tight_layout()
    do_plot(fig.add_subplot(211), df_fn, n1)
    do_plot(fig.add_subplot(212), df_ncn, n2)

    # fig.savefig("tcrs_noise_e2e.png", bbox_inches='tight')
    plt.show()
