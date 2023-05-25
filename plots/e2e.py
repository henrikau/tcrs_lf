#!/usr/bin/env python3
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import statistics

path=os.path.abspath(os.path.dirname(sys.argv[0]))
sys.path.append('{}/net_chan/plots'.format(os.path.dirname(os.path.dirname(path))))
print(sys.path)
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

def analyze_e2e(df, title):
    df['diff_ns'] = df['t2'] - df['t1']
    df['diff_ms'] = df['diff_ns']/1e6
    df['diff_us'] = df['diff_ns']/1e3
    df['date'] = pd.to_datetime(df['t1'],unit='ns')
    df['sma_ms'] = tc.sma(df['diff_ms'], 100)
    print(title)
    print("Count: {}".format(len(df['diff_us'])))
    print("Max: {:9.3f} us".format(max(df['diff_us'])))
    print("Min: {:9.3f} us".format(min(df['diff_us'])))
    print("Avg: {:9.3f} us".format(statistics.mean(df['diff_us'])))
    print("Std: {:9.3f} us".format(statistics.stdev(df['diff_us'])))

def plot_e2e(df, title):
    df.plot(x='date', y=['diff_ms', 'sma_ms'], alpha=0.4, color='red');
    plt.xlim((df['date'].iloc[0], df['date'].iloc[-1]))
    plt.title(title)


if __name__ == "__main__":
    df_fi = pd.read_csv('../tcrs_dataset/federated_e2e_idle.csv')
    df_fi = df_fi.drop([0])
    df_fn = pd.read_csv('../tcrs_dataset/federated_e2e_noise.csv')
    df_nci = pd.read_csv('../tcrs_dataset/netchan_e2e_idle.csv')
    df_ncn = pd.read_csv('../tcrs_dataset/netchan_e2e_noise.csv')

    analyze_e2e(df_fi, "Federated, Idle")
    analyze_e2e(df_fn, "Federated, Noise")
    analyze_e2e(df_nci, "NetChan, Idle")
    analyze_e2e(df_ncn, "NetChan, Noise")

    fig = plt.figure(num=None, figsize=(20, 12),
                     dpi=150,
                     facecolor='w', edgecolor='k')
    plt.tight_layout()

    ax1 = fig.add_subplot(211)
    ax1.set_title("Federated, idle")
    ax1.plot(df_fi['date'], df_fi['diff_ms'], alpha=0.4, color='red', label="E2E")
    ax1.plot(df_fi['date'], df_fi['sma_ms'], alpha=1, color='red', label="E2E (sma)")
    ax1.set_xlim((df_fi['date'].iloc[0], df_fi['date'].iloc[-1]))
    ax1.set_ylabel("E2E (ms)")
    ax1.legend(shadow=True, loc='upper right')

    ax2 = fig.add_subplot(212)
    ax2.set_title("NetChan, noise")
    ax2.plot(df_ncn['date'], df_ncn['diff_ms'], alpha=0.4, color='green', label="E2E")
    ax2.plot(df_ncn['date'], df_ncn['sma_ms'], alpha=1, color='green', label="E2E (sma)")
    ax2.set_xlim((df_ncn['date'].iloc[0], df_ncn['date'].iloc[-1]))

    ax2.set_xlabel("Time")
    ax2.set_ylabel("E2E (ms)")
    ax2.legend(shadow=True, loc='upper right')
    fig.savefig("e2e.png", bbox_inches='tight')
    plt.show();
