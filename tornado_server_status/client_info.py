#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
@author: h12345jack
@file: client_info.py
@time: 2022/03/21
"""

import os
import re
import time
import logging
from collections import defaultdict

import asyncio
import asyncssh

asyncssh.logging.set_log_level(logging.WARNING)

TIMEOUT = 10.0

async def run_cmdline_get_out(conn, cmdline, timeout=TIMEOUT):
    result = await asyncio.wait_for(conn.run(cmdline), timeout=timeout)
    return result.stdout


async def get_uptime(conn):
    cmdline = 'cat /proc/uptime'
    result = await run_cmdline_get_out(conn, cmdline)

    uptime = result.splitlines()[0].split('.', 2)
    uptime = int(uptime[0])
    days = int(uptime/60.0/60.0/24.0)
    hours = int(uptime/60.0/60.0)
    mins  = int(uptime/60.0 % 60)
    secs  = int(uptime % 60)

    if days > 0:
        return f'{days} 天'
    else:
        return f'{hours}:{mins}:{secs}'


async def get_time(conn):
    cmdline = 'cat /proc/stat'
    out = await run_cmdline_get_out(conn, cmdline)
    time_list = out.split(' ')[2:6]
    for i in range(len(time_list)):
        time_list[i] = int(time_list[i])
    return time_list


async def get_cpu(conn):
    # TODO change to multiple cpu 
    x = await get_time(conn)
    await asyncio.sleep(0.5)
    y = await get_time(conn)
    for i in range(len(x)):
        y[i] -= x[i]
    t = y
    st = sum(t)
    if st == 0:
        st = 1
    result = 100-(t[len(t)-1]*100.00/st)
    return round(result, 1)


async def get_loadavg(conn):
    cmdline = 'python3 -c "import os;print(os.getloadavg())"'
    out = await run_cmdline_get_out(conn, cmdline)
    return eval(out)


async def get_liuliang(conn):
    net_in = 0
    net_out = 0
    cmdline = 'cat /proc/net/dev'
    out = await run_cmdline_get_out(conn, cmdline)

    for line in out.split('\n'):
        netinfo = re.findall('([^\s]+):[\s]{0,}(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', line)
        if netinfo:
            if netinfo[0][0] == 'lo' or 'tun' in netinfo[0][0] \
                    or 'docker' in netinfo[0][0] or 'veth' in netinfo[0][0] \
                    or 'br-' in netinfo[0][0] or 'vmbr' in netinfo[0][0] \
                    or 'vnet' in netinfo[0][0] or 'kube' in netinfo[0][0] \
                    or netinfo[0][1] == '0' or netinfo[0][9] == '0':
                continue
            else:
                net_in += int(netinfo[0][1])
                net_out += int(netinfo[0][9])
    return net_in, net_out


async def get_memory(conn):
    cmdline = 'cat /proc/meminfo'
    out = await run_cmdline_get_out(conn, cmdline)

    re_parser = re.compile(r'^(?P<key>\S*):\s*(?P<value>\d*)\s*kB')
    memory_info = dict()
    for line in out.split('\n'):
        match = re_parser.match(line)
        if not match:
            continue
        key, value = match.groups(['key', 'value'])
        memory_info[key] = int(value)
    MemTotal = float(memory_info['MemTotal'])
    MemUsed = MemTotal-float(memory_info['MemFree'])-float(memory_info['Buffers'])-float(memory_info['Cached'])-float(memory_info['SReclaimable'])
    SwapTotal = float(memory_info['SwapTotal'])
    SwapFree = float(memory_info['SwapFree'])
    return int(MemTotal), int(MemUsed), int(SwapTotal), int(SwapFree)


async def get_hdd(conn):
    cmdline = 'df -Tlm --total -t ext4 -t ext3 -t ext2 -t reiserfs -t jfs -t ntfs -t fat32 -t btrfs -t fuseblk -t zfs -t simfs -t xfs'
    out = await run_cmdline_get_out(conn, cmdline)

    total = out.splitlines()[-1]
    used = total.split()[3]
    size = total.split()[2]
    return int(size), int(used)


async def get_net_speed(conn):
    netSpeed = {
        'netrx': [0.0],
        'nettx': [0.0],
        'clock': [0.0],
        'diff' : [0.0],
        'avgrx': [0],
        'avgtx': [0]
    }

    cmdline = 'cat /proc/net/dev'
    for _ in range(3):
        out = await run_cmdline_get_out(conn, cmdline)
        net_dev = out.splitlines()
        avgrx = 0
        avgtx = 0
        for dev in net_dev[2:]:
            dev = dev.split(':')
            if "lo" in dev[0] or "tun" in dev[0] \
                    or "docker" in dev[0] or "veth" in dev[0] \
                    or "br-" in dev[0] or "vmbr" in dev[0] \
                    or "vnet" in dev[0] or "kube" in dev[0]:
                continue
            dev = dev[1].split()
            avgrx += int(dev[0])
            avgtx += int(dev[8])
        now_clock = time.time()
        netSpeed["diff"].append(now_clock - netSpeed["clock"][-1])
        netSpeed["clock"].append(now_clock)
        netSpeed["netrx"].append(int((avgrx - netSpeed["avgrx"][-1]) / netSpeed["diff"][-1]))
        netSpeed["nettx"].append(int((avgtx - netSpeed["avgtx"][-1]) / netSpeed["diff"][-1]))
        netSpeed["avgrx"].append(avgrx)
        netSpeed["avgtx"].append(avgtx)

    def return_average_value(v_l):
        # due to the first one is zero
        return sum(v_l) / (len(v_l) - 1)
    netSpeed["diff"]  = return_average_value(netSpeed['diff'])
    netSpeed["clock"] = return_average_value(netSpeed['clock'])
    netSpeed["netrx"] = return_average_value(netSpeed["netrx"])
    netSpeed["nettx"] = return_average_value(netSpeed["nettx"])
    netSpeed["avgrx"] = return_average_value(netSpeed["avgrx"])
    netSpeed["avgtx"] = return_average_value(netSpeed["avgtx"])

    return netSpeed


async def get_tupd(conn):
    '''
    tcp, udp, process, thread count: for view ddcc attack , then send warning
    :return:
    '''
    cmdline = "ss -t|wc -l"
    s = await run_cmdline_get_out(conn, cmdline)
    t = int(s[:-1])-1
    cmdline = "ss -u|wc -l"
    s = await run_cmdline_get_out(conn, cmdline)
    u = int(s[:-1])-1
    cmdline = "ps -ef|wc -l"
    s = await run_cmdline_get_out(conn, cmdline)
    p = int(s[:-1])-2
    cmdline = "ps -eLf|wc -l"
    s = await run_cmdline_get_out(conn, cmdline)
    d = int(s[:-1])-2
    return t, u, p, d

# async get_ping_thread(conn):

async def get_virt_type(conn):
    cmdline = """
_exists() {
    local cmd="$1"
    if eval type type > /dev/null 2>&1; then
        eval type "$cmd" > /dev/null 2>&1
    elif command > /dev/null 2>&1; then
        command -v "$cmd" > /dev/null 2>&1
    else
        which "$cmd" > /dev/null 2>&1
    fi
    local rt=$?
    return ${rt}
}
cname=$( awk -F: '/model name/ {name=$2} END {print name}' /proc/cpuinfo | sed 's/^[ \t]*//;s/[ \t]*$//' )
_exists "dmesg" && virtualx="$(dmesg 2>/dev/null)"
if _exists "dmidecode"; then
    sys_manu="$(dmidecode -s system-manufacturer 2>/dev/null)"
    sys_product="$(dmidecode -s system-product-name 2>/dev/null)"
    sys_ver="$(dmidecode -s system-version 2>/dev/null)"
else
    sys_manu=""
    sys_product=""
    sys_ver=""
fi
if   grep -qa docker /proc/1/cgroup; then
    virt="Docker"
elif grep -qa lxc /proc/1/cgroup; then
    virt="LXC"
elif grep -qa container=lxc /proc/1/environ; then
    virt="LXC"
elif [[ -f /proc/user_beancounters ]]; then
    virt="OpenVZ"
elif [[ "${virtualx}" == *kvm-clock* ]]; then
    virt="KVM"
elif [[ "${cname}" == *KVM* ]]; then
    virt="KVM"
elif [[ "${cname}" == *QEMU* ]]; then
    virt="KVM"
elif [[ "${virtualx}" == *"VMware Virtual Platform"* ]]; then
    virt="VMware"
elif [[ "${virtualx}" == *"Parallels Software International"* ]]; then
    virt="Parallels"
elif [[ "${virtualx}" == *VirtualBox* ]]; then
    virt="VirtualBox"
elif [[ -e /proc/xen ]]; then
    virt="Xen"
elif [[ "${sys_manu}" == *"Microsoft Corporation"* ]]; then
    if [[ "${sys_product}" == *"Virtual Machine"* ]]; then
        if [[ "${sys_ver}" == *"7.0"* || "${sys_ver}" == *"Hyper-V" ]]; then
            virt="Hyper-V"
        else
            virt="Microsoft Virtual Machine"
        fi
    fi
else
    virt="Dedicated"
fi
echo $virt
    """

    out = await run_cmdline_get_out(conn, cmdline)
    return out.strip()


async def get_ip_country(conn):
    py_code = "import json; import urllib.request; f=urllib.request.urlopen('http://ipinfo.io');jd=json.loads(f.read());f.close();print(jd['country'])"
    cmdline = f'python3 -c "{py_code}"'
    out = await run_cmdline_get_out(conn, cmdline)
    return out.strip()


async def get_stats_data(conn, first_query=True):
    tasks = []
    results = []

    data = defaultdict(int)

    tasks.append(get_cpu(conn))
    results.append('cpu')
    
    tasks.append(get_uptime(conn))
    results.append('uptime')

    tasks.append(get_loadavg(conn))
    results.append(('load_1', 'load_5', 'load_15'))

    tasks.append(get_memory(conn))
    results.append(('memory_total', 'memory_used', 'swap_total', 'swap_free'))

    tasks.append(get_hdd(conn))
    results.append(('hdd_total', 'hdd_used'))

    tasks.append(get_net_speed(conn))
    results.append('netSpeed')

    tasks.append(get_liuliang(conn))
    results.append(('network_in', 'network_out'))
    # # todo：兼容旧版本，下个版本删除ip_status
    data['ip_status'] = True
    # data['ping_10010'] = lostRate.get('10010') * 100
    # data['ping_189'] = lostRate.get('189') * 100
    # data['ping_10086'] = lostRate.get('10086') * 100

    # data['time_10010'] = pingTime.get('10010')
    # data['time_189'] = pingTime.get('189')
    # data['time_10086'] = pingTime.get('10086')
    tasks.append(get_tupd(conn))
    results.append(('tcp', 'udp', 'process', 'thread'))

    if first_query:
        tasks.append(get_virt_type(conn))
        results.append('type')

        tasks.append(get_ip_country(conn))
        results.append('location')


    R_s = await asyncio.gather(*tasks)
    for l, r in zip(results, R_s):
        if isinstance(l, tuple):
            for l_1, r_1 in zip(l, r):
                data[l_1] = r_1
        else:
            data[l] = r       
    data['load'] = f"{data['load_1'], data['load_5'], data['load_15']}"
    data['swap_used'] = data['swap_total'] - data['swap_free']
    data['network_rx'] = data['netSpeed'].get("netrx", 0.0)
    data['network_tx'] = data['netSpeed'].get("nettx", 0.0)

    return data


async def test():
    hostname = '127.0.0.1'
    username = 'root'
    port = 22
    async with asyncssh.connect(hostname, username=username, port=port, known_hosts=None) as conn:
        data = await get_stats_data(conn)
        print(data)


if __name__ == '__main__':
    asyncio.run(test())
