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


def read_gptp_file(fpath, smalen=-1):
    """
    Read PTP log to extract clock accuracy
    """
    obj = re.compile("""
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

    df['rms_savg'] = tc.sma(df['rms'], smalen)
    df['time_raw'] = df['time']
    df['time'] = df['time'] - df['time'].iloc[0]

    return df


class gPTP:
    def  __init__(self, path1, path2, label1, label2):
        self.path1 = path1
        self.path2 = path2
        self.label1 = label1
        self.label2 = label2
        self.smalen = 600
        dfl = read_gptp_file(path1, self.smalen)
        dft = read_gptp_file(path2, self.smalen)
        self.df = pd.merge(dfl, dft, on=['time_raw'], suffixes=['_l', '_t'])
        self.df['time'] = self.df['time_raw'] - self.df['time_raw'].iloc[0]
        self._show_avg = False
        self.save_fig = False
        self.figname = "gptp_rms"
        self.folder = None
        self.kernel = None
        self.extra = None


    def set_folder(self, folder, fig="gptp_rms"):
        print("Setting folder for output: {}".format(folder))
        self.save_fig = True
        self.folder = folder
        self.figname = fig


    def show_avg(self):
        print("showing avg")
        self._show_avg = True


    def get_stats(self, listener=True):
        if listener:
            return len(self.df['time_raw']), \
                max(self.df['rms_l']), \
                min(self.df['rms_l']), \
                statistics.mean(self.df['rms_l']), \
                statistics.stdev(self.df['rms_l'])

        return len(self.df['time_raw']), max(self.df['rms_t']), \
            min(self.df['rms_t']), \
            statistics.mean(self.df['rms_t']), \
            statistics.stdev(self.df['rms_t'])


    def table_summary(self, kernel=None, extra=None):
        if kernel:
            self.kernel = kernel
        if extra:
            self.extra = kernel

        res = "Printing summary of:\n"
        res += "\t{}\n".format(self.path1)
        res += "\t{}\n".format(self.path2)
        res += "window length: {}\n\n".format(self.smalen)
        res += "{}|{:^20s}|{:^20s}\n".format(" "*10, self.label1, self.label2)
        if self.kernel and self.extra:
            tmp = "{} - {}".format(kernel, extra)
            t = "{:^53s}\n".format(tmp)
            res,t=t,res
            res += t

        res += "{}+{}+{}+\n".format("-"*10, "-"*20, "-"*20)
        cnt1,ma1,mi1,avg1,stdev1 = self.get_stats(True)
        cnt2,ma2,mi2,avg2,stdev2 = self.get_stats(False)

        start = int(self.df['time_raw'].iloc[0])
        end = int(self.df['time_raw'].iloc[-1])
        dur = str(datetime.timedelta(seconds=(end-start)))
        res += "{:>9s} | {:^40s}\n".format("duration", dur)
        res += "{:>9s} | {:23d}\n".format("SMA", self.smalen)
        res += "{:>9s} | {:15d}    | {:15d}\n".format("count", cnt1, cnt2)
        res += "{:>9s} | {:15d} ns | {:15d} ns\n".format("max", ma1, ma2)
        res += "{:>9s} | {:15d} ns | {:15d} ns\n".format("min", mi1, mi2)
        res += "{:>9s} | {:15.3f} ns | {:15.3f} ns\n".format("avg", avg1, avg2)
        res += "{:>9s} | {:15.3f} ns | {:15.3f} ns\n".format("stdev", stdev1, stdev2)
        return res

    def __str__(self):
        return self.table_summary()


    def _rms(self, ax, title):
        # Machine A
        ax.plot(self.df['time'], self.df['rms_savg_l'],
                color='blue', label="{}".format(self.label1))
        ax.plot(self.df['time'], self.df['rms_l'], color='blue', alpha=0.2,)

        # Machine B
        ax.plot(self.df['time'], self.df['rms_savg_t'],
                color='green', label="{}".format(self.label2))
        ax.plot(self.df['time'], self.df['rms_t'], color='green', alpha=0.2)

        if self._show_avg:
            avg = statistics.mean(self.df['rms_l'])
            ax.plot(self.df['time'], [avg]*len(self.df['time']), color='red',
                     label="{} avg: {:.3f}".format(self.label1, avg))

            avg = statistics.mean(self.df['rms_t'])
            ax.plot(self.df['time'], [avg]*len(self.df['time']), color='red',
                     label="{} avg: {:.3f}".format(self.label2, avg))

        ax.set_title("{} gPTP error".format(title), fontsize=BIGGER_SIZE)
        ax.set_xlabel("Time (sec)")
        ax.set_ylabel("RMS (ns)")
        ax.legend()
        ax.set_xlim((self.df['time'].iloc[0],self.df['time'].iloc[-1]))


    def _hist(self, ax, title = None):
        b = 25
        self.df['rms_l'].hist(ax=ax,
                              color='blue', alpha=0.3,
                              label="gPTP RMS {}".format(self.label1))
        self.df['rms_t'].hist(ax=ax,
                              color='green', alpha=0.3,
                              label="gPTP RMS {}".format(self.label2))
        ax.set_xlim((min(0, min(self.df['rms_t']), min(self.df['rms_l'])),
                     max(max(self.df['rms_t']), max(self.df['rms_l']))))

        if title:
            ax.set_title("{} gPTP RMS".format(title))
        ax.set_xlabel("RMS (ns)")
        ax.legend()


    def plot_all(self, title, rms_only=False):
        fig = plt.figure(num=None, figsize=(20, 12),
                         dpi=150,
                         facecolor='w', edgecolor='k')

        plt.tight_layout()
        self._rms(fig.add_subplot(211), title)
        if not rms_only:
            self._hist(fig.add_subplot(212))


        plt.legend(shadow=True)
        if self.folder:
            fig.savefig("{}/{}.png".format(self.folder, self.figname), bbox_inches='tight')
            # fig.savefig("{}/{}.svg".format(self.folder, self.figname), bbox_inches='tight')
            # fig.savefig("{}/{}.eps".format(self.folder, self.figname), bbox_inches='tight')
            with open("{}/{}.log".format(self.folder, self.figname), "w") as f:
                f.write(self.__str__())
            print("Saved to {}/{}.png (and svg)".format(self.folder, self.figname))


            targetImage = Image.open("{}/{}.png".format(self.folder, self.figname))
            cnt1,ma1,mi1,avg1,stdev1 = self.get_stats(True)
            metadata = PngInfo()
            metadata.add_text("gPTP/listener", self.label1)
            metadata.add_text("gPTP/listener/count", str(cnt1))
            metadata.add_text("gPTP/listener/max", str(ma1))
            metadata.add_text("gPTP/listener/min", str(mi1))
            metadata.add_text("gPTP/listener/avg", str(avg1))
            metadata.add_text("gPTP/listener/stdev", str(stdev1))

            cnt2,ma2,mi2,avg2,stdev2 = self.get_stats(False)
            metadata.add_text("gPTP/talker", self.label2)
            metadata.add_text("gPTP/talker/count", str(cnt2))
            metadata.add_text("gPTP/talker/max", str(ma2))
            metadata.add_text("gPTP/talker/min", str(mi2))
            metadata.add_text("gPTP/talker/avg", str(avg2))
            metadata.add_text("gPTP/talker/stdev", str(stdev2))
            targetImage.save("{}/{}.png".format(self.folder, self.figname), pnginfo=metadata)

        else:
            plt.show()
