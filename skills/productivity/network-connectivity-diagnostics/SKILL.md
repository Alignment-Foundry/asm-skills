---
name: network-connectivity-diagnostics
description: "Diagnose why a network service or device is unreachable — systematic trace from the service layer down to the WiFi/network config layer."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [networking, diagnostics, printers, wifi, troubleshooting]
    category: productivity
---

# Network Connectivity Diagnostics

Systematic approach to diagnosing why a network service (printer, NAS, server) is unreachable — especially after infrastructure changes like security hardening, router firmware updates, or network reconfiguration.

## Triggers

- User reports "I can't print to my network printer"
- User says "[something] stopped working after [someone] hardened/updated the network"
- User asks "check my printer/config/network connection"
- Any "was working, stopped after change" symptom on the local network

## Diagnostic Ladder — Bottom-Up

Start from the application layer and drill down. This ordering answers "is this a software config issue or a network issue?" before you start scanning.

### 1. Check application/service layer (CUPS for printers)

```bash
lpstat -t                         # scheduler, printers, status, jobs
lpstat -v                         # device URIs (reveals connection method)
lpstat -l -p <printer-name>       # detailed status + alerts
lpoptions -p <printer-name> -l    # PPD options
lpq -P <printer-name>             # job queue
```

**Key signals:**
- URI starts with `dnssd://` → printer discovered via mDNS/Bonjour — if mDNS fails, the printer becomes unreachable
- URI starts with `socket://` or `ipp://` → direct IP connection — check if IP changed
- "connecting-to-device" alert → CUPS can reach the queue but not the printer hardware
- "disabled since..." with cups-browsed error → remote printer discovery failure

Check CUPS error log:
```bash
cat /var/log/cups/error_log | grep -iE "printer|error|fail|dnssd" | tail -20
```

Check CUPS config for listen addresses (restrictive config can block network printing):
```bash
cat /etc/cups/cupsd.conf | grep -iE "Listen|Port|Allow|Deny"
```

### 2. Check if the device is on the network

```bash
# Quick host discovery (requires nmap)
nmap -sn 192.168.1.0/24

# Check for specific printer ports
nmap -p 9100,631,515 192.168.1.0/24

# Check ARP table
arp -a

# Check mDNS/DNS-SD discovery
avahi-browse -a -t          # list all discovered services (install avahi-utils if needed)
avahi-browse -rt _pdl-datastream._tcp    # look for network printers
avahi-browse -rt _ipp._tcp               # look for IPP printers
```

**Key signals:**
- Only 2 hosts (router + your machine) → the target device is not on the network at all
- Device responded but wrong IP → DHCP lease changed or static config lost
- mDNS service not found → printer WiFi disconnected or mDNS blocked

### 3. Check your own network connection

```bash
# Current interface and IP
ip -4 addr show

# Active WiFi connection
nmcli dev status
nmcli con show --active

# Current connection details (SSID, BSSID, security)
nmcli -s con show <connection-name> | grep -iE "ssid|band|bssid|security|psk"
```

### 4. Identify recent network changes

```bash
# When did the WiFi connection change?
journalctl -u NetworkManager --since "3 days ago" | grep -iE "connect|disconnect|wifi|activation|password"

# Look for SSID switches — especially from one profile to another
journalctl -u NetworkManager --since "3 days ago" | grep "connection-add-activate\|new-activation"
```

Compare old vs new network profiles:
```bash
# All stored connections (including ones not currently active)
nmcli con show

# Compare security settings between old and new
nmcli -s con show <old-ssid> | grep -E "ssid|psk|security|key-mgmt"
nmcli -s con show <new-ssid> | grep -E "ssid|psk|security|key-mgmt"
```

### 5. Check system-level network config

```bash
# Firewall rules
sudo nft list ruleset       # modern (nftables)
sudo iptables -L -n         # legacy (iptables)
sudo ufw status verbose     # ufw frontend

# mDNS/DNS-SD services
systemctl status avahi-daemon
systemctl status cups-browsed

# Multicast groups (mDNS uses 224.0.0.251:5353)
ip maddr show <interface>
cat /proc/sys/net/ipv4/conf/*/mc_forwarding
```

## Root Causes Found in Practice

### Pattern: Hardening profile changed the WiFi SSID + password

Most common with security/audit teams. The machine is moved to a new SSID (e.g., `ATKM → ATKM2`) with a different password. Network printers, IoT devices, and other peripherals remain on the **old** SSID or lose connectivity entirely.

**Symptom:** nmap shows only 2 hosts (your machine + router). Printer mDNS not found. CUPS shows "connecting-to-device."

**Fix:** Reconfigure the printer to connect to the new SSID with the new password, via the printer's front panel (Settings → Network → Wireless LAN → Setup Wizard).

### Pattern: Router DHCP lease changed or device switched to static IP

**Symptom:** Direct IP printers (`socket://` or `ipp://` URIs) fail. Printer has a different IP than what CUPS expects.

**Fix:** Assign a DHCP reservation on the router for the printer's MAC address, or update the CUPS printer URI with `lpadmin -p <name> -v <new-uri>`.

### Pattern: Firewall blocking mDNS multicast (224.0.0.251:5353)

**Symptom:** `avahi-browse` returns nothing. Printer using `dnssd://` URI is not found even though it's on the network.

**Fix:** Allow mDNS traffic through the firewall: `sudo ufw allow 5353/udp` or adjust nftables rules.

### Pattern: Client isolation on router separates WiFi clients

**Symptom:** Both your machine and the printer are on the same WiFi network but can't reach each other. Printer is visible via `nmap` from a wired device but not from WiFi.

**Fix:** Disable "AP Isolation" / "Client Isolation" / "Wireless Isolation" on the router's WiFi settings.

## Tools You'll Need

| Tool | Install | Purpose |
|------|---------|---------|
| `nmap` | `apt install nmap` | Network discovery and port scanning |
| `avahi-utils` | `apt install avahi-utils` | mDNS/DNS-SD browsing and resolution |
| `nmcli` | `apt install network-manager` (pre-installed) | WiFi connection profile management |

## Reference File

See `references/phonesec-printer-hardening-example.md` for a full worked example: diagnosing a Brother MFC-7360N that went offline after a security hardening profile changed the WiFi SSID and password.

## Pitfalls

- **`avahi-browse` vs `avahi-resolve`**: These are in the `avahi-utils` package, which is **not** installed by default alongside `avahi-daemon`. If the commands are missing, install the utils package rather than assuming mDNS is broken.
- **`sudo` required for firewall inspection**: `nft list ruleset` and `iptables -L` need root. If the user's account lacks sudo, try non-root approaches first (check kernel modules with `lsmod | grep nf_`, check sysctl for network hardening).
- **mDNS URIs are dynamic**: A `dnssd://` printer URI means CUPS will re-resolve the IP on every job. If mDNS stops working (or the printer disappears from the network), the URI becomes dead. Consider switching to a direct `socket://ip:9100` URI if the printer supports it — this bypasses mDNS entirely.
- **nmcli shows password hashes, not cleartext**: The `psk` field in `nmcli -s con show` will show the actual WiFi password. Be careful where you display/report it.
- **Journalctl timestamps**: NetworkManager logs timestamps in local time. Cross-reference with `lpstat` timestamps to correlate when the printer last worked vs when the network changed.
- **SSID name != network capability**: A hardened SSID might use the same security type (WPA2-PSK) but a different password. Always compare the actual credentials, not just the protocol.
