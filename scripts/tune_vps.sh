#!/bin/bash
# Run once on the Contabo VPS after provisioning.
# Usage: bash scripts/tune_vps.sh

echo "=== Tuning VPS for high-concurrency SMTP verification ==="

# 1. Raise file descriptor limits
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "root soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "root hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# 2. Kernel network tuning
sudo tee -a /etc/sysctl.conf <<EOF
# Email verifier tuning
fs.file-max = 200000
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1024 65535
net.core.somaxconn = 65535
net.ipv4.tcp_fin_timeout = 15
net.core.netdev_max_backlog = 65535
EOF

# 3. Apply without reboot
sudo sysctl -p

echo "=== Done. Logout and back in for ulimit changes to take effect. ==="
echo "=== Then start the app with: ==="
echo "    ulimit -n 65536 && uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --loop uvloop"
