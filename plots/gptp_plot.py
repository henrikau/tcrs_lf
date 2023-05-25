#!/usr/bin/env python3
import os
import sys

path=os.path.abspath(os.path.dirname(sys.argv[0]))
sys.path.append('{}/net_chan/plots'.format(os.path.dirname(os.path.dirname(path))))
from lib.gPTP import *
from lib.clock_realtime import *
from lib import *
import 
if __name__ == "__main__":
    print("PTP Federated case:\n{}".format("="*100))
    fgptpl = "../tcrs_dataset/listener_ptp_federated.log"
    fgptpt = "../tcrs_dataset/talker_ptp_federated.log"

    fptp = gPTP.gPTP(fgptpl, fgptpt, "Listener", "Talker")
    fclock = clock_realtime.clock(fgptpl, fgptpt, "Listener", "Talker")
    print("5.16.2-rt19 - LF Federated Test run")
    print(fclock)
    print(fptp)
    fptp.set_folder(".", "gptp_rms_federated")
    fptp.plot_all("5.16.2-rt19 - LF Federated Test run")

    print("PTP NetChan case:\n{}".format("="*100))
    ncgptpl = "../tcrs_dataset/listener_ptp_netchan.log"
    ncgptpt = "../tcrs_dataset/talker_ptp_netchan.log"
    ncptp = gPTP.gPTP(ncgptpl, ncgptpt, "Listener", "Talker")
    ncclock = clock_realtime.clock(ncgptpl, ncgptpt, "Listener", "Talker")
    print("5.16.2-rt19 - LF NetChan Test run")
    print(ncclock)
    print(ncptp)
    ncptp.set_folder(".", "gptp_rms_netchan")
    ncptp.plot_all("5.16.2-rt19 - LF NetChan Test run")
