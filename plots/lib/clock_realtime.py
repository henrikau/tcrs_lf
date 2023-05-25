"""
Foo
"""
import re
from dateutil.parser import parse
import pandas as pd
import statistics
import datetime
import matplotlib.pyplot as plt
import lib.timedc_lib as tc
from PIL import Image
from PIL.PngImagePlugin import PngInfo

SMALL_SIZE = 12
MEDIUM_SIZE = 17
BIGGER_SIZE = 24

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=MEDIUM_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=MEDIUM_SIZE)    # legend fontsize
plt.rc('figure', titlesize=50)  # fontsize of the figure title


def read_gptp_file(fpath):
    """
    Read PTP log to extract clock accuracy from both ptp4l and phc2sys
    """
    obj_ptp = re.compile("""
^[a-zA-Z]*[\s]+[\d]*[\s]*
([\d]{2}\:[\d]{2}\:[\d]{2})[\s]* # time
[a-zA-z0-9]*[\s]*
ptp4l\:[\s]*
\[
([\d]*\.[\d]*)                  # timestamp
\][\s]*
rms[\s]*
([\d]*)
[\s]*max[\s]*
(-?[\d]*)                       # rms
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
    obj_phc2sys = re.compile("""
^[a-zA-Z]*[\s]+[\d]*[\s]*
([\d]{2}\:[\d]{2}\:[\d]{2})[\s]* # time
[a-zA-z0-9]*[\s]*
phc2sys\:[\s]*
\[
([\d]*\.[\d]*)                  # timestamp
\][\s]*
CLOCK_REALTIME[\s]+phc[\s]+offset[\s]+
(-?[\d]*)                       # offset
.*
    """, re.VERBOSE|re.UNICODE)

    hdr = ['time', 'rms', 'phc']
    values = []
    current = {}
    with open(fpath) as f:
        for line in f.readlines():
            ptp_match = obj_ptp.match(line.strip())
            phc2sys_match = obj_phc2sys.match(line.strip())
            if ptp_match:
                if current:
                    print("missed a phc2sys-value")
                    current = {}
                current['time'] = parse(ptp_match.group(1), fuzzy=True).timestamp()
                current['rms'] = ptp_match.group(3)
            elif phc2sys_match:
                if current:
                    ts = parse(phc2sys_match.group(1), fuzzy=True).timestamp()
                    offset = phc2sys_match.group(3)

                    # We do not match on timestamp as phc2sys always
                    # follows ptp4l, however, if we have 2 consecutive
                    # of any kind, we only use the closest values
                    values.append([ts, current['rms'], offset])
                    current = {}

    df = pd.DataFrame(columns=hdr, data=values)
    types = {'time'    : 'int',
             'rms'     : 'int',
             'phc'     : 'int'}
    df = df.astype(types)
    df['time_raw'] = df['time']
    df['time'] = df['time'] - df['time'].iloc[0]
    df['aggregated_abs'] = abs(df['rms']) + abs(df['phc'])
    return df


class clock:
    def  __init__(self, path1, path2, label1, label2):
        self.path1 = path1
        self.path2 = path2
        self.label1 = label1
        self.label2 = label2

        dfl = read_gptp_file(path1)
        dft = read_gptp_file(path2)
        self.df = pd.merge(dfl, dft, on=['time_raw'], suffixes=['_l', '_t'])

    def get_stats(self, listener=True):
        if listener:
            return len(self.df['time_raw']), \
                max(self.df['aggregated_abs_l']), \
                statistics.mean(self.df['aggregated_abs_l']), \
                statistics.stdev(self.df['aggregated_abs_l'])

        return len(self.df['time_raw']), \
            max(self.df['aggregated_abs_t']), \
            statistics.mean(self.df['aggregated_abs_t']), \
            statistics.stdev(self.df['aggregated_abs_t'])


    def table_summary(self):
        res = ""
        res += "{}|{:^20s}|{:^20s}\n".format(" "*10, self.label1, self.label2)
        res += "{}+{}+{}+\n".format("-"*10, "-"*20, "-"*20)
        cnt1,ma1,avg1,stdev1 = self.get_stats(listener=True)
        cnt2,ma2,avg2,stdev2 = self.get_stats(listener=False)

        start = int(self.df['time_raw'].iloc[0])
        end = int(self.df['time_raw'].iloc[-1])
        dur = str(datetime.timedelta(seconds=(end-start)))
        res += "{:>9s} | {:^40s}\n".format("duration", dur)
        res += "{:>9s} | {:15d}    | {:15d}\n".format("count", cnt1, cnt2)
        res += "{:>9s} | {:15d} ns | {:15d} ns\n".format("max", ma1, ma2)
        res += "{:>9s} | {:15.3f} ns | {:15.3f} ns\n".format("avg", avg1, avg2)
        res += "{:>9s} | {:15.3f} ns | {:15.3f} ns\n".format("stdev", stdev1, stdev2)
        return res

    def __str__(self):
        return self.table_summary()

