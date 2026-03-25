#!/bin/bash
DEVICE_ID="0069724F-E1EA-42D1-809F-F9D7C54DF7D6"
xcrun simctl openurl $DEVICE_ID "kaka://" || true
sleep 2

# Type Username
xcrun simctl io $DEVICE_ID type "kanae"
sleep 1
# Tap next/done to move to password (depends on UI) or just tab if hardware keyboard is on
xcrun simctl io $DEVICE_ID type "\n"
sleep 1
# Type Password
xcrun simctl io $DEVICE_ID type "Huahua1122"
sleep 1
xcrun simctl io $DEVICE_ID type "\n"
