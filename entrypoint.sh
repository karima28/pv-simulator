#!/bin/bash

echo "Starting Meter Simulation..."
python meter.py &

# Wait a few seconds to let meter.py start publishing
sleep 10

echo "Starting PV Simulator..."
python pv_simulator.py