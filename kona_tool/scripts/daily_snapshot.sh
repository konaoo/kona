#!/bin/bash
set -e

APP_DIR="/home/ec2-user/portfolio/kona_tool"
LOG_DIR="${APP_DIR}/archive/logs"
mkdir -p "${LOG_DIR}"

ts=$(date +%Y%m%d_%H%M%S)
curl -s -X POST "http://127.0.0.1:5003/api/snapshot/trigger" > "${LOG_DIR}/snapshot_${ts}.log"
