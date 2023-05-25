import re
from dateutil.parser import parse
import pandas as pd
import statistics
import matplotlib.pyplot as plt


def sma(vals, winsize = 10):
    """
    Create a dataset of sliding avg
    """
    valsize = len(vals)
    res = []
    offset = int(winsize / 2)
    idx = offset
    res = [sum(vals[idx - offset : idx + offset]) / winsize] * offset
    sma = 0
    while (idx+offset) < valsize:
        sma = sum(vals[idx - offset : idx + offset]) / winsize
        res.append(sma)
        idx += 1
    # make sure we pad the tail so we keep the dimensions
    while len(res) < len(vals):
        res.append(sma)

    return res


def ptp_rms_statistics(df):
    rms_max = max(df['rms'])
    rms_min = min(df['rms'])
    rms_avg = statistics.mean(df['rms'])
    rms_std = statistics.stdev(df['rms'])
    return (rms_max, rms_min, rms_avg, rms_std)


# ---------------------------------------------------------------------------- #
#          Read data
# ---------------------------------------------------------------------------- #
def read_gptp_file(fpath, smalen=-1):
    """
    Read PTP log to extract clock accuracy
    """
    obj = re.compile("""
^[a-zA-Z]*[\s][\d]*[\s]*
([\d]{2}\:[\d]{2}\:[\d]{2})[\s]* # time
[a-zA-z0-9]*[\s]*
ptp4l\:[\s]*
\[
([\d]*\.[\d]*)                  # timestamp
\][\s]*
rms[\s]*
([\d]*)
[\s]*max[\s]*
(-?[\d]*)                       # max
[\s]*freq[\s]*
(-?[\d]*)                       # freq
[\s]*\+/\-[\s]*
(-?[\d]*)                       # +/- freq
[\s]*delay[\s]*
(-?[\d]*)                       # delay
[\s]*\+/\-[\s]*
(-?[\d]*)                       # +/-delay
.*
    """, re.VERBOSE|re.UNICODE)
    hdr = ['time', 'ts', 'rms', 'max', 'freq', 'freqadj', 'delay', 'delayadj']
    values = []
    with open(fpath) as f:
        for line in f.readlines():
            match = obj.match(line.strip())
            if match:
                values.append([parse(match.group(1), fuzzy=True).timestamp(),
                               match.group(2),
                               match.group(3),
                               match.group(4),
                               match.group(5),
                               match.group(6),
                               match.group(7),
                               match.group(8)])

    df = pd.DataFrame(columns=hdr, data=values)
    types = {'time'    : 'int',
             'ts'      : 'float',
             'rms'     : 'int',
             'max'     : 'int',
             'freq'    : 'int',
             'freqadj' : 'int',
             'delay'   : 'int',
             'delayadj': 'int',
             }
    df = df.astype(types)
    if smalen < 0:
        smalen = int(len(df['rms'].values)/10)
    df['rms_savg'] = sma(df['rms'], smalen)
    df['time_raw'] = df['time']
    df['time'] = df['time'] - df['time'].iloc[0]
    return df


def read_gptp_merged(bpath="/home/henrikau/dev/timedc_work/code/testruns/idle", bfile="gptp_nort"):
    dfl = read_gptp_file("{}/{}_listener.log".format(bpath, bfile))
    dft = read_gptp_file("{}/{}_talker.log".format(bpath, bfile))
    dfm = pd.merge(dfl, dft, on=['time_raw'], suffixes=['_l', '_t'])
    return dfm


def read_packet_frames(bpath="/home/henrikau/dev/timedc_work/code/testruns", case=""):
    listener = pd.read_csv("{}/netfifo_listener{}.csv".format(bpath, case))
    talker = pd.read_csv("{}/netfifo_talker{}.csv".format(bpath, case))

    merged = pd.merge(listener, talker, on=['stream_id', 'seqnr', 'avtp_ns'], suffixes=['_l', '_t'])
    merged['delay_ns'] = merged['recv_ptp_ns_l'] - merged['cap_ptp_ns_t']
    merged['time_ns'] = merged['cap_ptp_ns_t'] - merged['cap_ptp_ns_t'].iloc[0]
    merged['delay_ns_sma'] = sma(merged['delay_ns'], 50)
    return merged


def read_delay_frames(base, case=""):
    listener = pd.read_csv("{}/netfifo_listener{}.csv_d".format(base, case))
    talker = pd.read_csv("/{}/netfifo_talker{}.csv_d".format(base, case))
    merged = pd.merge(listener, talker, on=['ptp_target'], suffixes=['_l', '_t'])
    merged['error_l_ns'] = merged['cpu_target_l'] - merged['cpu_actual_l']
    merged['ptp_wakeup_l'] = merged['ptp_target'] - merged['error_l_ns']
    merged['error_l_sma'] = sma(merged['error_l_ns'], 50)
    merged['time_ns'] = merged['ptp_target'] - merged['ptp_target'].iloc[0]
    merged['error_t_ns'] = merged['cpu_target_t'] - merged['cpu_actual_t']
    merged['ptp_wakeup_t'] = merged['ptp_target'] - merged['error_t_ns']
    merged['error_t_sma'] = sma(merged['error_t_ns'], 50)


    # PTP target - error_listener: actual wakeup listener
    # PTP target - error_talker : actual wakeup talker
    # actual wakeup talker - actual wakeup listener: relative error
    # ptp - e_l - (ptp-e_t) = -e_l + e_t = e_t - e_l
    merged['error_both'] = merged['error_t_ns'] - merged['error_l_ns']
    merged['error_both_sma'] = sma(merged['error_both'], 50)
    return merged


def print_ptp_rms_stats(df, name):
    rms_max, rms_min, rms_avg, rms_std = ptp_rms_statistics(df)
    print("{} rms summary ({} samples seen)".format(name, len(df['rms'])))
    print("\tmax: {:3d} ns".format(rms_max))
    print("\tmin: {:3d} ns".format(rms_min))
    print("\tavg: {:7.3f} ns".format(rms_avg))
    print("\tstd: {:7.3f} ns".format(rms_std))


def print_delay_stats(df):
    print("Delay stats for frame, {} samles seen".format(len(df['delay_ns'])))
    print("Max: {:.3f} us, min: {:.3f} us".format(max(df['delay_ns'])/1000.0, min(df['delay_ns']) / 1000.0))
    print("avg: {:.3f} ns".format(statistics.mean(df['delay_ns'])))
    print("std: {:.3f} ns".format(statistics.stdev(df['delay_ns'])))


def print_stats(merged, case):
    print("Statistics for {}, {} samples".format(case, len(merged['time_ns'])))
    print("Talker:")
    print(" * max: {} ns".format(max(merged['error_t_ns'])))
    print(" * min: {} ns".format(min(merged['error_t_ns'])))
    print(" * avg: {:.3f} ns".format(statistics.mean(merged['error_t_ns'])))
    print(" * stdev: {:.3f} ns".format(statistics.stdev(merged['error_t_ns'])))
    print("Listener:")
    print(" * max: {} ns".format(max(merged['error_l_ns'])))
    print(" * min: {} ns".format(min(merged['error_l_ns'])))
    print(" * avg: {:.3f} ns".format(statistics.mean(merged['error_l_ns'])))
    print(" * stdev: {:.3f} ns".format(statistics.stdev(merged['error_l_ns'])))
    print("Relative error:")
    print(" * max: {} ns".format(max(merged['error_both'])))
    print(" * min: {} ns".format(min(merged['error_both'])))
    print(" * avg: {:.3f} ns".format(statistics.mean(merged['error_both'])))
    print(" * stdev: {:.3f} ns".format(statistics.stdev(merged['error_both'])))



# ---------------------------------------------------------------------------- #
#          Plots
# ---------------------------------------------------------------------------- #
def plot_gptp_rms(df1, df2, title, label='Full RT'):
    plt.title(title)
    plt.xlabel("Time (seconds) since start")
    plt.ylabel("gPTP RMS (ns)")
    plt.plot(df1['time'],       df1['rms_savg'], color='blue', label="TSN1 {} (swa)".format(label))
    plt.plot(df1['time'],       df1['rms'],      color='blue', alpha=0.2, label="TSN1 {}".format(label))
    plt.plot(df2['time'],       df2['rms_savg'], color='green', label="TSN2 {} (swa)".format(label))
    plt.plot(df2['time'],       df2['rms'],      color='green', alpha=0.2, label="TSN2 {}".format(label))

    plt.xlim((min(df1['time'].iloc[0], df2['time'].iloc[0]), 
              max(df1['time'].iloc[-1], df2['time'].iloc[-1])))
    plt.legend(shadow=True)
    plt.show()

def plot_delay_trace(df, title=None):
    plt.plot(df['time_ns'], df['error_l_ns'], alpha=0.2, color='r')
    plt.plot(df['time_ns'], df['error_l_sma'], color='r', label='Error (Listener)')
    plt.plot(df['time_ns'], df['error_t_ns'], alpha=0.2, color='b')
    plt.plot(df['time_ns'], df['error_t_sma'], color='b', label='Error (Talker)')
    plt.plot(df['time_ns'], df['error_both'], color='g', alpha=0.2)
    plt.plot(df['time_ns'], df['error_both_sma'], color='g', label='Relative error (talker-listener)')
    plt.legend()
    plt.ylabel("Error (ns)")
    plt.xlabel("Time (ns)")
    plt.xlim((df['time_ns'].iloc[0], df['time_ns'].iloc[-1]))
    #plt.ylim((min(0, min(df['error_l_ns'])), max(df['error_l_ns'])*1.05))
    plt.plot()
    if title:
        plt.title(title)
    plt.show()




def plot_packet_trace(df, title=None):
    plt.plot(df['time_ns'], df['delay_ns'], alpha=0.2, color='r')
    plt.plot(df['time_ns'], df['delay_ns_sma'], color='r')
    plt.xlim((df['time_ns'].iloc[0], df['time_ns'].iloc[-1]))
    plt.ylim((min(0, min(df['delay_ns'])), max(df['delay_ns'])*1.05))
    t = "Transportation delay"
    if title:
        t += "\n" + title
    plt.title(t)
    plt.show()
