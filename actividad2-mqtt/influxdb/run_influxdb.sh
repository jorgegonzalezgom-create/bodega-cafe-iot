#!/bin/bash
# InfluxDB 2 en la EC2 privada. Uso: INFLUX_TOKEN=... INFLUX_PASSWORD=... ./run_influxdb.sh
sudo docker run -d --name influxdb --restart always \
  -p 8086:8086 \
  -v influx_data:/var/lib/influxdb2 \
  -e DOCKER_INFLUXDB_INIT_MODE=setup \
  -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
  -e DOCKER_INFLUXDB_INIT_PASSWORD=$INFLUX_PASSWORD \
  -e DOCKER_INFLUXDB_INIT_ORG=bodega \
  -e DOCKER_INFLUXDB_INIT_BUCKET=lecturas \
  -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=$INFLUX_TOKEN \
  influxdb:2.7
