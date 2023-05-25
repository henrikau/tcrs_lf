import pandas as pd
import statistics
import matplotlib.pyplot as plt
import lib.timedc_lib as tc
import numpy as np
import datetime


class PktDelay:
    def  __init__(self, lfile, tfile, label1, label2, find_dropped=True):
        self.listener = pd.read_csv(lfile)
        self.talker = pd.read_csv(tfile)
        self.title = None
        self.save_fig = False
        self.find_dropped = find_dropped

        # Merge l & t
        self.df = pd.merge(self.listener, self.talker, on=['stream_id', 'seqnr', 'avtp_ns'], suffixes=['_l', '_t'])
        self.df['time_ns_rel'] = self.df['cap_ptp_ns_t'] - self.df['cap_ptp_ns_t'].iloc[0]

        # E2E delay
        self.df['e2e_ns'] = self.df['recv_ptp_ns_l'] - self.df['cap_ptp_ns_t']
        self.df['e2e_ns_sma'] = tc.sma(self.df['e2e_ns'], 500)
        self.e2e_min = min(self.df['e2e_ns'])
        self.e2e_max = max(self.df['e2e_ns'])
        self.e2e_avg = statistics.mean(self.df['e2e_ns'])
        self.e2e_std = statistics.stdev(self.df['e2e_ns'])

        # Arrival period
        prev = self.df['recv_ptp_ns_l'].iloc[0]
        diffs = [self.df['recv_ptp_ns_l'].iloc[1] - prev]
        for val in self.df['recv_ptp_ns_l'][1:]:
            diffs.append(val-prev)
            prev = val
        self.df['recv_del_ns'] = diffs
        self.df['recv_del_sma'] = tc.sma(diffs, 500)
        self.period_min = min(self.df['recv_del_ns'])
        self.period_max = max(self.df['recv_del_ns'])
        self.period_avg = statistics.mean(self.df['recv_del_ns'])
        self.period_std = statistics.stdev(self.df['recv_del_ns'])

        # Tx period
        prev = self.df['cap_ptp_ns_t'].iloc[0]
        diff_tx = [self.df['cap_ptp_ns_t'].iloc[1]-prev]
        for val in self.df['cap_ptp_ns_t'][1:]:
            diff_tx.append(val-prev)
            prev = val
        self.df['tx_del_ns'] = diff_tx
        self.df['tx_del_sma'] = tc.sma(diff_tx, 500)
        self.tx_period_min = min(self.df['tx_del_ns'])
        self.tx_period_max = max(self.df['tx_del_ns'])
        self.tx_period_avg = statistics.mean(self.df['tx_del_ns'])
        self.tx_period_std = statistics.stdev(self.df['tx_del_ns'])

        # Find dropped frames
        if self.find_dropped:
            m = pd.merge(self.listener, self.talker,
                         on=['stream_id', 'seqnr', 'avtp_ns'],
                         how='right',
                         suffixes=['_l', '_t'])
            m['time_ns_rel'] = m['cap_ptp_ns_t'] - m['cap_ptp_ns_t'].iloc[0]
            m['e2e_ns'] = m['recv_ptp_ns_l'] - m['cap_ptp_ns_t']

            self.dropped_map = m['cap_ptp_ns_l'].isnull()
            self.dropped = m[self.dropped_map]

            m['throughput'] = -self.e2e_max
            m.throughput[self.dropped_map] = self.e2e_max
            self.m = m


    def set_folder(self, folder):
        self.save_fig = True
        self.folder = folder
        print("Saving plots to {}".format(self.folder))


    def set_title(self, title):
        self.title = title

    def __str__(self):
        res = "E2E Delay\n"
        if self.title:
            res += "{}\n".format(self.title)


        end = self.df['time_ns_rel'].iloc[-1] / 1e9
        res += "Duration: {}\n".format(datetime.timedelta(seconds=end))
        res += "Samples:  {}\n".format(len(self.df['e2e_ns']))
        res += "Max: {:10,} ns\n".format(self.e2e_max)
        res += "Min: {:10,} ns\n".format(self.e2e_min)
        res += "avg: {:14.3f} ns\n".format(self.e2e_avg)
        res += "std: {:14.3f} ns\n".format(self.e2e_std)
        # res += "\n"
        # res += "Packet arrival periodicity\n"
        # res += "Samples: {}\n".format(len(self.df['recv_del_ns']))
        # res += "Max: {:14.3f} us\n".format(self.period_max / 1000.0)
        # res += "Min: {:14.3f} us\n".format(self.period_min / 1000.0)
        # res += "avg: {:14.3f} us\n".format(self.period_avg / 1000.0)
        # res += "std: {:14.3f} us\n".format(self.period_std / 1000.0)
        res += "\n"
        if self.find_dropped:
            res += "Dropped frames\n"
            res += "Count: {}\n".format(len(self.dropped))


        return res


    def e2e_all(self, title=""):
        fig = plt.figure(num=None, figsize=(24,13.5), dpi=160, facecolor='w', edgecolor='k')
        plt.tight_layout()
        self._e2e_scatter(fig.add_subplot(311), title)
        self._e2e_scatter(fig.add_subplot(312), title, True)
        self._e2e_hist(fig.add_subplot(325), title)
        self._e2e_hist(fig.add_subplot(326), title, True)

        if self.save_fig:
            fig.savefig("{}/frame_e2e_delay_all.png".format(self.folder), bbox_inches='tight')


    def period_all(self, title=""):
        fig = plt.figure(num=None, figsize=(24,13.5), dpi=160, facecolor='w', edgecolor='k')
        plt.tight_layout()
        self._period_scatter(fig.add_subplot(321), title, do_rx = True, do_filter = False)
        self._period_scatter(fig.add_subplot(322), title, do_rx = True, do_filter = True)
        self._period_scatter(fig.add_subplot(323), title, do_rx = False, do_filter = False)
        self._period_scatter(fig.add_subplot(324), title, do_rx = False, do_filter = True)

        self._period_hist(fig.add_subplot(325), title, False)
        self._period_hist(fig.add_subplot(326), title, True)
        if self.save_fig:
            fig.savefig("{}/frame_period_delay_all.png".format(self.folder), bbox_inches='tight')

    def plot_all(self, title):
        self.e2e_all(title)
        self.period_all(title)
        if not self.save_fig:
            plt.show()
        else:
            with open("{}/frame_delay.log".format(self.folder), "w") as f:
                f.write(self.__str__())

    # -----------------------------------#
    #              Internal              #
    # -----------------------------------#

    def _e2e_scatter(self, ax, title, do_filter=False, overlay_avg=True):
        title = "{} E2E frame delay\nMax: {:.3f} us, min: {:.3f}, avg: {:.3f}, $\sigma$: {:.3f}"\
            .format(title, self.e2e_max/1000.0, self.e2e_min/1000.0,
                    self.e2e_avg/1000.0, self.e2e_std/1000.0)

        if do_filter:
            upper = self.e2e_avg + 3*self.e2e_std
            lower = self.e2e_avg - 3*self.e2e_std
            mmap = ((self.df['e2e_ns'] < upper) & (self.df['e2e_ns'] > lower))
            ax.plot(self.df.time_ns_rel[mmap],
                    self.df.e2e_ns[mmap], 'o',
                    alpha=0.2, color='green', label="E2E delay, within 3 $\sigma$")

            ax.plot(self.df['time_ns_rel'],
                    self.df['e2e_ns_sma'],
                    color='blue',
                    alpha=0.9,
                    label="E2E delay (sma)")
            title ="+/- 3 $\sigma$ ({:.3f} us, {:.3f} us)".format(lower/1000.0, upper/1000.0)
        else:
            ax.plot(self.df.time_ns_rel, self.df.e2e_ns, 'o', alpha=0.9, color='green', label="E2E delay")

        if overlay_avg:
            ax.plot(self.df['time_ns_rel'], [self.e2e_avg]*len(self.df['time_ns_rel']),
                    color='red',
                    alpha=0.7,
                    label="Avg E2E delay")

        ax.set_title(title)
        ax.set_xlim((min(self.df['time_ns_rel'].iloc[0],  self.df['time_ns_rel'].iloc[0]),
                     max(self.df['time_ns_rel'].iloc[-1], self.df['time_ns_rel'].iloc[-1])))
        ax.set_ylabel("Delay (ns)")
        ax.legend()


    def _e2e_hist(self, ax, title, do_filter=False):
        b = 500
        title = "{} E2E Delay histogram".format(title)
        if do_filter:
            upper = self.e2e_avg + 3*self.e2e_std
            lower = self.e2e_avg - 3*self.e2e_std
            mmap = ((self.df['e2e_ns'] < upper) & (self.df['e2e_ns'] > lower))
            e2e_min = min(self.df.e2e_ns[mmap])
            e2e_max = max(self.df.e2e_ns[mmap])
            self.df.e2e_ns[mmap].hist(ax=ax, bins=b, color='blue', alpha=0.3, label="E2E delay < 3 x $\sigma$")
            ax.set_xlim((e2e_min, e2e_max))
            title = "+/- 3 $\sigma$ ({:.3f} us,{:.3f} us)".format(lower/1000.0, upper/1000.0)
        else:
            self.df['e2e_ns'].hist(ax=ax, bins=b, color='blue', alpha=0.3, label="E2E delay")

        ax.set_title(title)
        ax.set_xlabel("E2E delay (ns)")


    def _period_scatter(self, ax, title, do_rx=True, do_filter=False):
        direction = "Rx"
        if not do_rx:
            direction = "Tx"
        title = "{} {} Frame periodicity".format(title, direction)

        pmax = self.period_max
        pmin = self.period_min
        pavg = self.period_avg
        pstd = self.period_std
        delns = self.df['recv_del_ns']
        delsma = self.df['recv_del_sma']
        color='green'
        if not do_rx:
            pmax = self.tx_period_max
            pmin = self.tx_period_min
            pavg = self.tx_period_avg
            pstd = self.tx_period_std
            delns = self.df['tx_del_ns']
            delsma = self.df['tx_del_sma']
            color='blue'

        title += "\n{} Max: {:.3f} us, min: {:.3f} us, avg: {:.3f} us, $\sigma$: {:.3f} us"\
            .format(direction, pmax/1000.0, pmin/1000.0, pavg/1000.0, pstd/1000.0)

        if do_filter:
            upper = pavg + 3*pstd
            lower = pavg - 3*pstd

            mmap = ((delns < upper) & (delns > lower))
            ax.plot(self.df.time_ns_rel[mmap], delns[mmap],
                    'o', alpha=0.1, color=color, label="Periodicity (ns) +/- 3$\sigma$")
            ax.plot(self.df['time_ns_rel'], delsma,
                    alpha=0.7, color='yellow', label="Periodicity (sma)")

            if self.find_dropped:
                # self.dropped['dropped'] = [self.e2e_max] * len(self.dropped)
                ax.plot(self.dropped.time_ns_rel, [upper]*len(self.dropped),
                        'x', alpha=1.0, color='red',
                        label="Dropped frames")
                title = "+/- 3$\sigma$ ({:.3f},{:.3f} us)".format(lower/1000.0, upper / 1000.0)

        else:
            ax.plot(self.df['time_ns_rel'], delns,
                    'o', alpha=0.1, color=color, label="Time between frames (ns)")

            if self.find_dropped:
                ax.plot(self.dropped['time_ns_rel'], self.dropped['dropped'],
                        'x', alpha=1.0, color='red',
                        label="Dropped frames")

        # ax.plot(self.df['time_ns_rel'],
        #         [pavg]*len(self.df['time_ns_rel']),
        #         color='red', alpha=0.7, label="Avg ({:.3f} us)".format(self.period_avg / 1000.0))

        ax.set_title(title)
        # ax.set_xlim((min(self.df['time_ns_rel'].iloc[0],  self.df['time_ns_rel'].iloc[0]),
        #              max(self.df['time_ns_rel'].iloc[-1], self.df['time_ns_rel'].iloc[-1])))
        ax.set_ylabel("Period (ns)")
        ax.legend()


    def _period_hist(self, ax, title, do_filter=False):
        b = 500
        title = "{}, Frame period".format(title)
        if do_filter:
            upper = self.period_avg + 3*self.period_std
            lower = self.period_avg - 3*self.period_std
            mmap = ((self.df['recv_del_ns'] < upper) & (self.df['recv_del_ns'] > lower))
            period_min = min(self.df.recv_del_ns[mmap])
            period_max = max(self.df.recv_del_ns[mmap])

            tx_upper = self.tx_period_avg + 3*self.tx_period_std
            tx_lower = self.tx_period_avg - 3*self.tx_period_std
            tx_mmap = ((self.df['tx_del_ns'] < tx_upper) & (self.df['tx_del_ns'] > tx_lower))
            tx_period_min = min(self.df.tx_del_ns[mmap])
            tx_period_max = max(self.df.tx_del_ns[mmap])

            self.df.recv_del_ns[mmap].hist(ax=ax, bins=b, color='green', alpha=0.3, label="Rx, $\sigma$={:.3f} $\mu$s".format(self.period_std/1000.0))
            self.df.tx_del_ns[tx_mmap].hist(ax=ax, bins=b, color='blue', alpha=0.3, label="Tx, $\sigma$={:.3f} $\mu$s".format(self.tx_period_std/1000.0))
        else:
            self.df['recv_del_ns'].hist(ax=ax, bins=b, color='green', alpha=0.3, label="Packet Rx delay")
            self.df['tx_del_ns'].hist(ax=ax, bins=b, color='blue', alpha=0.3, label="Packet Tx delay")


        ax.legend()
        ax.set_title(title)
        ax.set_xlabel("Packet period (ns)")


    def plot_packet_trace(self, title=None):
        plt.plot(self.df['time_ns_rel'], self.df['delay_ns'], alpha=0.2, color='r')
        plt.plot(self.df['time_ns_rel'], self.df['delay_ns_sma'], color='r')
        plt.xlim((self.df['time_ns_rel'].iloc[0], self.df['time_ns_rel'].iloc[-1]))
        plt.ylim((min(0, min(self.df['delay_ns'])), max(self.df['delay_ns'])*1.05))
        if title:
            plt.title(title)
        plt.show()

    def plot_periodic(self, title=""):
        """
        Look at time between each frame
        """
        fig = plt.figure(num=None, figsize=(24,13.5), dpi=80, facecolor='w', edgecolor='k')
        plt.tight_layout()
        self._diff_e2e_plot(fig.add_subplot(221), title)
        self._diff_period_plot(fig.add_subplot(222), title)
        self._e2e_hist_plot(fig.add_subplot(223), title)
        self._period_hist_plot(fig.add_subplot(224), title)
        plt.show()

