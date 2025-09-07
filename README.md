# PV Simulator Application

A Python 3 application designed to simulate typical household photovoltaic (PV) power production and consumption. 
It uses RabbitMQ as a message broker and Docker for containerization. The PV power generation is an estimation based on 
the provided power profile, while the power consumption is estimated from an external publication (ref: 
https://www.researchgate.net/publication/337446929_Smart_Meter_Privacy). The results are recorded in a csv file saved to
the root directory.

---

## 📋 Application Overview

The application consists of the following components:

- **Meter**: Simulates household power consumption based on a realistic hourly profile. It generates readings every 5 seconds (configurable) from midnight to 23:59:59 and sends them to a RabbitMQ queue named meterreadings. Each 
- message includes a timestamp and the power value in kW.
- **Broker**: RabbitMQ is used as the message broker to pass data between the meter and the pv simulator.
- **PV Simulator**: Listens to the RabbitMQ queue for meter power consumption values, generates simulated PV 
- production values, takes the difference between them to calculate the power surplus (a positive value indicates a 
- surplus, while a negative value indicates a shortage - meaning the remaining power is drawn from grid), and writes 
- the results to a file.
- **Output File (pv_simulator_24hrs.csv)**: Contains timestamped entries with meter value (Power Consumption in kW), 
- PV value (Power Generation in kW), and their difference (Power Surplus in kW).

---

## Requirements

- Python 3.x
- Docker Desktop
- RabbitMQ (via Docker)
- `pika` Python library

---

## Project Structure

PVSim/
├── Dockerfile
├── entrypoint.sh
├── run_simulator.sh
├── requirements.txt
├── meter.py
├── pv_simulator.py
└── README.md

---

## Quick Start

To run the simulator:

```bash
./run_simulator.sh
```

This will:
- Start RabbitMQ in Docker
- Build the simulator image
- Run the simulator and generate pv_simulator_24hrs.csv
RabbitMQ dashboard: [http://localhost:15672](http://localhost:15672)  
Login: `guest` / `guest`

---

## Manual Setup Instructions

### 1. Start RabbitMQ Locally

```bash
docker run -d --hostname rabbitmq --name rabbitmq \
  -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

RabbitMQ UI: http://localhost:15672
Login: guest / guest

If you get a name conflict error, run docker rm -f rabbitmq to remove the old container and try again.

### 2. Build Simulator Image

```bash
docker build -t pv-simulator .
```

### 3. Run the Simulator

```bash
docker run --rm --name pv-sim \
  -e RABBITMQ_HOST=host.docker.internal \
  pv-simulator

```

### 4. Copy the file out

```bash
docker cp pv-sim:/PVSim/pv_simulator_24hrs.csv ./pv_simulator_24hrs.csv
```

