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
