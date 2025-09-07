import random
from datetime import datetime, time, timedelta
import csv
import pika
import json
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logging.info("Script started")

received_meter_readings_dict ={}

# create a csv file 'pv_simulator_24hrs.csv' to write to with the following headers:
# Time, Power Consumption (kW), Power Generation (kW), Power Surplus (kW)
with (open('pv_simulator_24hrs.csv', 'w')) as csvfile:
    header_row = ['Time', 'Power Consumption (kW)', 'Power Generation (kW)', 'Power Surplus (kW)']
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerow(header_row)


def receive_meter_reading_from_broker():
    # to receive the meter readings from the RabbitMQ broker
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'host.docker.internal')
    credentials = pika.PlainCredentials('guest', 'guest')
    # parameters = pika.ConnectionParameters(host='127.0.0.1', port=5672, credentials=credentials)
    parameters = pika.ConnectionParameters(host=rabbitmq_host, port=5672, credentials=credentials)

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue='meterreadings', durable=True)

    def callback(ch, method, properties, body):
        # the meter readings were sent to the broker as [timestamp, meter reading] json data
        # deserialized to Python list object
        logging.info(f"Received message: {body}")
        received_read = json.loads(body)
        current_time = received_read[0]
        power_consumption = received_read[1]
        # get the power generated at the given time
        power_generated = get_power_generation_pv(datetime.strptime(current_time, "%H:%M:%S"))

        # write the entries to the csv file 'pv_simulator_24hrs.csv'
        # including the surplus power, i.e. power_generated-power_consumption
        with (open('pv_simulator_24hrs.csv', 'a', newline='')) as csvfile1:
            writer1 = csv.writer(csvfile1, delimiter=',')
            writer1.writerow([current_time, power_consumption, power_generated, (power_generated-power_consumption)])

    channel.basic_consume(queue='meterreadings', on_message_callback=callback, auto_ack=True)
    try:
        logging.info("Waiting for messages.")
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()


def get_power_generation_pv(current_time):
    # given the current time, it returns the power generated in kW
    # power generation is roughly estimated from given sample power profile (assignment sheet)
    sample_pv_gen_reading = {0:0.0, 1:0.0, 2:0.0, 3:0.0, 4:0.0, 5:0.0, 6:0.1, 7:0.2, 8: 0.3, 9: 0.5, 10: 2.0, 11:2.5,
                            12:2.75, 13: 3.15, 14:3.25, 15:3.0, 16:3.15, 17: 2.75, 18: 2.0, 19: 1.5, 20: 0.1, 21: 0.0,
                            22: 0.0, 23: 0.0}

    # get the hour value for the current_time and get the corresponding reading from the defined list
    current_hour = current_time.hour
    pv_read = sample_pv_gen_reading.get(current_hour)
    # between 21:00 and 5:00 - there should be no sunlight (or at least we're assuming so for a specific season),
    # so it should be zero. Otherwise, add some randomness within a reasonable range (here set to -0.5 and 0.5)
    # to the reading
    if 5 < current_hour < 21:
        pv_read += random.uniform(-0.5, 0.5)

    # since pv generated cannot be negative, we set it to zero in case the random factor added causes it to become negative
    # if positive, just round to two decimal places
    check_for_positive_val = lambda x: round(x, 2) if x > 0 else 0.0
    return check_for_positive_val(pv_read)


def main():
    # calling the function to be able to receive the readings from the broker, initiates the whole process
    receive_meter_reading_from_broker()
    logging.info("Started consuming meter readings")


if __name__ == "__main__":
    main()
