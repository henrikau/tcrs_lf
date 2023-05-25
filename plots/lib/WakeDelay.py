import pandas as pd
import lib.timedc_lib as tc
import statistics
import matplotlib.pyplot as plt

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

class WakeDelay:
    def  __init__(self, lfile, tfile, label1, label2):
        self.label1 = label1
        self.label2 = label2
        self.save_fig = False
        self.folder = None
        self.figname = "wake_delay"

        listener = pd.read_csv(lfile)
        talker = pd.read_csv(tfile)

        merged = pd.merge(listener, talker, how='inner', on=['ptp_target'], suffixes=['_l', '_t'])
        merged['time_ns_rel'] = merged['ptp_target'] - merged['ptp_target'].iloc[0]

        # Listener
        merged['error_l_ns'] = merged['cpu_target_l'] - merged['cpu_actual_l']
        merged['error_l_sma'] = tc.sma(merged['error_l_ns'], 500)
        merged['ptp_wakeup_l'] = merged['ptp_target'] - merged['error_l_ns']
        self.minl = min(merged['error_l_ns'])
        self.maxl = max(merged['error_l_ns'])
        self.avgl = statistics.mean(merged['error_l_ns'])
        self.stdl = statistics.stdev(merged['error_l_ns'])

        # Talker
        merged['error_t_ns'] = merged['cpu_target_t'] - merged['cpu_actual_t']
        merged['error_t_sma'] = tc.sma(merged['error_t_ns'], 500)
        merged['ptp_wakeup_t'] = merged['ptp_target'] - merged['error_t_ns']
        self.mint = min(merged['error_t_ns'])
        self.maxt = max(merged['error_t_ns'])
        self.avgt = statistics.mean(merged['error_t_ns'])
        self.stdt = statistics.stdev(merged['error_t_ns'])

        # PTP target - error_listener: actual wakeup listener
        # PTP target - error_talker : actual wakeup talker
        # actual wakeup talker - actual wakeup listener: relative error
        # ptp - e_l - (ptp-e_t) = -e_l + e_t = e_t - e_l
        merged['error_both'] = merged['error_t_ns'] - merged['error_l_ns']
        merged['error_both_sma'] = tc.sma(merged['error_both'], 500)
        merged['time_s'] = merged['time_ns_rel']/1e9
        self.minr = min(merged['error_both'])
        self.maxr = max(merged['error_both'])
        self.avgr = statistics.mean(merged['error_both'])
        self.stdr = statistics.stdev(merged['error_both'])

        self.merged = merged
        self.dfl = listener
        self.dft = talker


    def set_folder(self, folder, fig="wake_delay"):
        self.save_fig = True
        self.folder = folder
        self.figname = fig
        print("Saving plots to {}".format(self.folder))


    def set_title(self, title):
        self.title = title

    def __str__(self):
        res = ""
        if self.title:
            res += "{}\n".format(self.title)
        res += "Task wakeup statistics, {} samples ({}: {}, {}: {})\n".format(len(self.merged['time_ns_rel']),
                                                                              self.label1,
                                                                              len(self.dfl['ptp_target']),
                                                                              self.label2,
                                                                              len(self.dft['ptp_target']))
        res += "{:10s}|{:^20s}|{:^20s}|{:^20s}\n".format("", self.label1, self.label2, "Relative error")
        res += "+{:s}+{:s}+{:s}+{:s}\n".format("-"*9, "-"*20,"-"*20,"-"*20)
        res += " {:9s}|{:>16d} ns |{:>16d} ns |{:>16d} ns\n".format("max", self.maxt, self.maxl, self.maxr)
        res += " {:9s}|{:>16d} ns |{:>16d} ns |{:>16d} ns\n".format("min", self.mint, self.minl, self.minr)
        res += " {:9s}|{:>16.3f} ns |{:>16.3f} ns |{:>16.3f} ns\n".format("avg", self.avgt, self.avgl, self.avgr)
        res += " {:9s}|{:>16.3f} ns |{:>16.3f} ns |{:>16.3f} ns\n".format("stdev", self.stdt, self.stdl, self.stdr)
        return res

    def _delay(self, ax, title, do_filter = False):
        title = "Wakeup Delay error\n{}".format(title)
        ax.plot(self.merged['time_s'], self.merged['error_l_ns'], alpha=0.2, color='r')
        ax.plot(self.merged['time_s'], self.merged['error_l_sma'], color='r', label='{}'.format(self.label1))
        ax.plot(self.merged['time_s'], self.merged['error_t_ns'], alpha=0.2, color='b')
        ax.plot(self.merged['time_s'], self.merged['error_t_sma'], color='b', label='{}'.format(self.label2))
        ax.plot(self.merged['time_s'], self.merged['error_both'], color='g', alpha=0.2)
        ax.plot(self.merged['time_s'], self.merged['error_both_sma'], color='g', label='Relative')
        ax.legend()
        ax.set_ylabel("Error (ns)")
        ax.set_xlabel("Time (sec)")
        ax.set_xlim((self.merged['time_s'].iloc[0], self.merged['time_s'].iloc[-1]))
        ax.set_title(title, fontsize=BIGGER_SIZE)

    def _delay_hist(self, ax, do_filter = False):
        b = 500
        # Reduce histogram to +/- 3 stdevs
        if do_filter:
            title = "Wakeup delays, filtered to +/- 3 $\sigma$"
            upper = self.avgl + 3 * self.stdl
            lower = self.avgl - 3 * self.stdl
            mmap = ((self.merged['error_l_ns'] < upper) & (self.merged['error_l_ns'] > lower))
            ll = len(self.merged.error_l_ns[mmap])

            self.merged.error_l_ns[mmap].hist(ax=ax, bins=b,
                                              color='red', alpha=0.3,
                                              label="{}".format(self.label1))
            upper = self.avgt + 3 * self.stdt
            lower = self.avgt - 3 * self.stdt
            mmap = ((self.merged['error_t_ns'] < upper) & (self.merged['error_t_ns'] > lower))
            lt = len(self.merged.error_t_ns[mmap])
            self.merged.error_t_ns[mmap].hist(ax=ax, bins=b,
                                              color='blue', alpha=0.3,
                                              label="{}".format(self.label2))
            upper = self.avgr + 3 * self.stdr
            lower = self.avgr - 3 * self.stdr
            mmap = ((self.merged['error_both'] < upper) & (self.merged['error_both'] > lower))
            lr = len(self.merged.error_both[mmap])
            self.merged.error_both[mmap].hist(ax=ax, bins=b,
                                              color='green', alpha=0.3,
                                              label="Relative")

        else:
            title = "Wakeup delays, {} bins".format(b)
            self.merged['error_l_ns'].hist(ax=ax, bins=b,
                                           color='red', alpha=0.3,
                                           label="{}, $\sigma$={:.3f} us".format(self.label1, self.stdl/1000.0))
            self.merged['error_t_ns'].hist(ax=ax, bins=b,
                                           color='blue', alpha=0.3,
                                           label="{}, $\sigma$={:.3f} us".format(self.label2, self.stdt/1000.0))
            self.merged['error_both'].hist(ax=ax, bins=b,
                                           color='green', alpha=0.3,
                                           label="Relative, $\sigma$={:.3f} us".format(self.stdr / 1000.0))
        ax.legend()
        ax.set_title(title, fontsize=BIGGER_SIZE-2)
        ax.set_xlabel("Wakeup error (ns)")


    def plot_delay(self, title=""):
        fig = plt.figure(num=None, figsize=(24,13.5), dpi=160, facecolor='w', edgecolor='k')
        plt.tight_layout()
        self._delay(fig.add_subplot(111), title)
        if self.save_fig:
            fig.savefig("{}/{}.png".format(self.folder, self.figname), bbox_inches='tight')
            with open("{}/{}.log".format(self.folder, self.figname), "w") as f:
                f.write(self.__str__())
        else:
            plt.show()

    def plot_all(self, title=""):
        fig = plt.figure(num=None, figsize=(24,13.5), dpi=160, facecolor='w', edgecolor='k')
        plt.tight_layout()
        self._delay(fig.add_subplot(211), title)
        self._delay_hist(fig.add_subplot(223))
        self._delay_hist(fig.add_subplot(224), True)
        if self.save_fig:
            fig.savefig("{}/{}_all.png".format(self.folder, self.figname), bbox_inches='tight')
            with open("{}/{}_all.log".format(self.folder, self.figname), "w") as f:
                f.write(self.__str__())
        else:
            plt.show()
