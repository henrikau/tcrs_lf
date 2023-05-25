import re
from dateutil.parser import parse
import matplotlib.pyplot as plt
import pandas as pd


# 2022-04-06 12:09:14 current bw:  831.726 Mbps (67686 pkts/sec - 83.173 %) (current max: 67686 of 81380
# 2022-04-06 12:09:15 current bw:  831.922 Mbps (67702 pkts/sec - 83.192 %) (current max: 67702 of 81380
# 2022-04-06 12:09:16 current bw:  831.689 Mbps (67683 pkts/sec - 83.169 %) (current max: 67702 of 81380
# 2022-04-06 12:09:17 current bw:  831.603 Mbps (67676 pkts/sec - 83.160 %) (current max: 67702 of 81380
def read_varnoise_file(logfile, ts_offset_sec):
    obj = re.compile("""
^([\d]{4}-[\d]{2}-[\d]{2})      # date
[\s]+
([\d]{2}\:[\d]{2}\:[\d]{2})     # tiem
[\s]+current[\s]bw\:[\s]+
([\d]*\.[\d]{3})                # bw
[\s]+Mbps[\s]+\(
([\d]+)                       # pkts
[\s]*pkts/sec[\s]-[\s]
([\d]+\.[\d]{3})
[\s]%\)[\s]\(current[\s]max:[\s]
([\d]+)
[\s]of[\s]
([\d]+)
.*
""", re.VERBOSE | re.UNICODE)
    hdr = ['ts', 'date', 'time', 'bwmbps', 'bwpst', 'pkts', 'pkts_max', 'pkts_bound']
    values = []
    with open(logfile, 'r') as f:
        for line in f.readlines():
            match = obj.match(line.strip())
            if match:
                date = match.group(1)
                time = match.group(2)
                bw = match.group(3)
                pkts = match.group(4)
                bw_pst = match.group(5)
                pkts_max = match.group(6)
                pkts_bound = match.group(7)
                ts = parse("{} {}".format(date, time), fuzzy=True).timestamp()
                values.append([ts, date, time, bw, bw_pst, pkts, pkts_max, pkts_bound])
    df = pd.DataFrame(columns=hdr, data=values)
    types = {'ts'     : 'int',
             'date'   : 'str',
             'time'   : 'str',
             'bwmbps' : 'float',
             'bwpst'  : 'float',
             'pkts'      : 'int',
             'pkts_max'  : 'int',
             'pkts_bound': 'int'
             }
    df = df.astype(types)
    df['ts'] = df['ts']
    df['time_rel'] = df['ts'] - df['ts'].iloc[0] + ts_offset_sec
    return df


class NetNoise:
    def __init__(self, logfile, title, offset_sec=0):
        print("reading and parsing {}, shifting ts {} secs".format(logfile, offset_sec))
        self.df = read_varnoise_file(logfile, offset_sec)
        self.title = title


    def __str__(self):
        res = "{}\n".format(self.title)
        res += "{} entries seen\n".format(len(self.df['ts']))
        return res


    def plot(self):
        plt.plot(self.df['time_rel'], self.df['bwmbps'], color='y')
        plt.show()
