#!/bin/bash
set -e
scp listener/src/listener.lf tsn2:dev/lf/listener/src/.
scp talker/src/talker.lf tsn1:dev/lf/talker/src/.
scp distributed/src/federated.lf tsn1:dev/lf/distributed/src/.
scp distributed/src/federated.lf tsn2:dev/lf/distributed/src/.
scp include/manifest.h tsn1:dev/lf/include/.
scp include/manifest.h tsn2:dev/lf/include/.
