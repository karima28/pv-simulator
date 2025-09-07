import random
from datetime import datetime, time, timedelta
import pika
import json
import os
import logging

#logging.basicConfig(level=logging.INFO)
#logging.info("Script started")

# setting starting time of simulation to midnight 00:00 and end time to 24 hours after
initial_time = time(0, 0)
end_time = time(23, 59, 59)
# after how many seconds a new meter reading is to be generated
time_to_new_reading_s = 5


def get_updated_time(initial_time, end_time, time_to_new_reading_s):
    # generator for creating timestamps given the initial and end times, plus the step between each timestamp in seconds
    # date is irrelevant - just using today's date to convert both initial_time and end_time
    # from datetime.time to datetime.datetime
    current_date = datetime.now().date()
    initial_datetime = datetime.combine(current_date, initial_time)
    end_datetime = datetime.combine(current_date, end_time)

    updated_datetime = initial_datetime

    while updated_datetime < end_datetime:
        yield updated_datetime
        updated_datetime += timedelta(seconds=time_to_new_reading_s)


# reference link for sample meter readings:
# https://www.researchgate.net/publication/337446929_Smart_Meter_Privacy
def get_power_consumption_meter(current_time):
    # given the time, it returns a power consumption meter reading

    # a sample meter reading in kW for each hour of the day, based on the ref link provided above
    sample_meter_reading = {0:1.0, 1:1.0, 2:1.0, 3:2.0, 4:2.0, 5:3.5, 6:3.5, 7: 3.0, 8: 3.0, 9: 3.0, 10: 5.0, 11:9.0,
                            12:8.0, 13: 8.0, 14:4.0, 15:2.0, 16:2.0, 17: 2.0, 18: 2.0, 19: 4.0, 20: 4.0, 21: 4.0,
                            22: 2.0, 23: 1.0}

    # the samples are estimated on an hourly basis, so only the hour part of the current time is required
    # and get the corresponding meter reading from the dict sample_meter_reading
    current_hour = current_time.hour
    meter_read = sample_meter_reading.get(current_hour)
    # add some randomness (with standard deviation 0.5kW)
    meter_read += random.uniform(-0.5, 0.5)
    return round(meter_read, 2)


def send_meter_reading_to_broker(timestamp, meter_reading):
    # using RabbitMQ as a broker to send the meter readings to photovoltaic simulator

    try:
        # Use 'localhost' on Linux
        rabbitmq_host = os.getenv('RABBITMQ_HOST', 'host.docker.internal')
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters(host=rabbitmq_host, port=5672, credentials=credentials)
        #parameters = pika.ConnectionParameters(host='127.0.0.1', port=5672, credentials=credentials)

        connection = pika.BlockingConnection(parameters)
        logging.info("Connected to RabbitMQ")

        channel = connection.channel()
        channel.queue_declare(queue='meterreadings', durable=True)

        message = json.dumps([timestamp, meter_reading])
        channel.basic_publish(
            exchange='',
            routing_key='meterreadings',
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
        )
        logging.info(f"Sent message: {message}")

        connection.close()
        logging.info("Connection closed")

    except Exception as e:
        logging.error(f"Failed to connect to RabbitMQ or send message: {e}")





for updated_time in get_updated_time(initial_time, end_time, time_to_new_reading_s):
    # for each timestamp generated using get_updated_time
    # based on the current time, get a household power consumption meter reading and send to the broker
    power_consumed = get_power_consumption_meter(updated_time)
    send_meter_reading_to_broker(datetime.strftime(updated_time, "%H:%M:%S"), power_consumed)