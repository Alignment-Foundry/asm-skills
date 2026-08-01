# Worked Example: Printer Disappeared After phonesec Hardening

## Scenario

A "phonesec" security hardening profile was applied to the network. Afterward, the Brother MFC-7360N network printer became unreachable. Both the HL-L3280CDW and MFC-7360N printers were affected.

## Timeline

1. **Before phonesec**: Machine connected to WiFi SSID `ATKM` with password `PurpleCoconut866!`. Printer was on the same network, discoverable via mDNS, printing worked.
2. **Jul 25, ~17:53**: phonesec created and activated a new connection profile `ATKM2` with password `eithervolume814`. Machine switched to ATKM2.
3. **After switch**: Printer (still configured for ATKM) dropped off the network. Only 2 hosts remained on 192.168.1.0/24.

## Diagnostic Commands Executed (in order)

```bash
# Step 1: Check CUPS status
lpstat -t
# → MFC-7360N idle/enabled but "connecting-to-device" alert
# → HL-L3280CDW disabled, cups-browsed: "No destination host name"

# Step 2: Check device URIs
lpstat -v
# → MFC-7360N: dnssd://Brother%20MFC-7360N._pdl-datastream._tcp.local/
# → HL-L3280CDW: implicitclass://Brother_HL_L3280CDW_series/

# Step 3: Network discovery
nmap -sn 192.168.1.0/24
# → Only 2 hosts: 192.168.1.1 (router), 192.168.1.78 (this machine)
# → PRINTER NOT FOUND

# Step 4: Specific port scan
nmap -p 9100,631,515 192.168.1.0/24
# → No printer ports open anywhere

# Step 5: Check WiFi connections
nmcli con show
# → ATKM (old, no longer active)
# → ATKM2 (active, current connection)

# Step 6: Compare connection details
nmcli -s con show ATKM | grep -iE "ssid|psk"
# → SSID: ATKM, PSK: PurpleCoconut866!

nmcli -s con show ATKM2 | grep -iE "ssid|psk"
# → SSID: ATKM2, PSK: eithervolume814

# Step 7: Find when the switch happened
journalctl -u NetworkManager --since "3 days ago" | grep "connection-add-activate"
# → Jul 25 17:53:03 — switch from ATKM to ATKM2 confirmed

# Step 8: Check mDNS services
systemctl status avahi-daemon
# → Running. Multicast group 224.0.0.251 (mDNS) was joined.

# Step 9: Check firewall (no rules found)
# No nftables, no iptables, no ufw — network issue, not firewall
```

## Root Cause

**The printer was still configured to connect to `ATKM`** with the old password. When phonesec created `ATKM2` (a different SSID with a different password) and moved the machine to it, the printer stayed on ATKM or lost connectivity entirely. Since both SSIDs appear on the same physical router but the passwords differ, the printer couldn't authenticate to ATKM2 and ATKM's password may also have been changed.

## Fix

Reconfigure the Brother MFC-7360N's WiFi from its front panel:
1. Menu → Network → Wireless LAN → Setup Wizard
2. Select SSID `ATKM2`
3. Enter password `eithervolume814`
4. Confirm and wait for connection

## Key Insight for Future Sessions

When a user reports "X stopped working after the security team hardened our network" and the device uses a `dnssd://` (mDNS/Bonjour) URI:

1. **The hardening profile likely changed the WiFi — not the device.** Check SSID and password differences between old and new connection profiles first.
2. Network printers using `dnssd://` are completely dependent on mDNS discovery. If the printer changes WiFi and the computer changes to a different WiFi, mDNS breaks even if they're on the same subnet.
3. No firewall rules found does not mean nothing changed — WiFi credential/SSID changes are invisible to firewall tools.
