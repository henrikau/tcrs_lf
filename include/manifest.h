/*
 * Copyright 2022 SINTEF AS
 *
 * This Source Code Form is subject to the terms of the Mozilla
 * Public License, v. 2.0. If a copy of the MPL was not distributed
 * with this file, You can obtain one at https://mozilla.org/MPL/2.0/
 */
#ifndef MANIFEST_H
#define MANIFEST_H
#include <netchan.h>
#define BUFFER_SIZE 10000

enum joints {
    BASE = 0,
    SHOULDER,
    ELBOW,
    W1,
    W2,
    W3,
    END,                        // not used, marker only
};

struct ur_state
{
	uint64_t seqnr;
	uint64_t ts_ns;
	double urts;
    double target_q[END];
	double actual_q[END];               // "actual_q"
	double actual_tcp_pose[END];        // "actual_TCP_pose"
	double actual_tcp_speed[END];       // "actual_TCP_speed"
} __attribute__((packed));
typedef struct ur_state ur_state_t;

struct ur_ctrl
{
    uint64_t seqnr;
    int32_t cmd;
    int32_t reserved;
    double in_tqd[END];
} __attribute__((packed));
typedef struct ur_ctrl  ur_ctrl_t;

#define NIC (char *)"lo"
    
struct sensor_data {
	uint64_t t1; // data sent
	uint64_t t2; // data received
	uint64_t data;
	uint64_t seqnr;
};
typedef struct sensor_data sensor_t;

struct net_fifo net_fifo_chans[] = {
	{
		/* DEFAULT_MCAST */
		.dst       = {0x01, 0x00, 0x5E, 0x00, 0xFE, 0x01},
		.stream_id = 1,
		.sc	   = CLASS_A,
		.size      = sizeof(struct ur_state),
		.freq      = 500,
		.name      = "urstate",
	},
	{
		/* DEFAULT_MCAST */
		.dst       = {0x01, 0x00, 0x5E, 0x00, 0xFE, 0x02},
		.stream_id = 2,
		.sc	   = CLASS_A,
		.size      = sizeof(struct ur_ctrl),
		.freq      = 500,
		.name      = "urctrl",
	},
	{
		/* DEFAULT_MCAST */
		.dst       = {0x01, 0x00, 0x5E, 0x01, 0x11, 0x03},
		.stream_id = 3,
		.sc        = CLASS_A,
		.size      = sizeof(struct sensor_data),
		.freq      = 10,
		.name      = "sensor_data",		
	},
};


#endif	/* MANIFEST_H */
