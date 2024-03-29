"""Email me when there will be a frost. This happens if the temperature is less
than 3 degrees. Not strictly true but good enough."""

import logging
import datetime
import smtplib
import os
from email.message import EmailMessage
from pyowm.owm import OWM
import datapoint
import config

logging.basicConfig()
logger = logging.getLogger(__name__)
if 'FROST_ALERT_LOG_LEVEL' in os.environ.keys():
    logger.setLevel(level=os.environ['FROST_ALERT_LOG_LEVEL'])
else:
    try:
        config.LOG_LEVEL
    except AttributeError:
        pass
    else:
        logger.setLevel(level=config.LOG_LEVEL)


def get_owm_temp():
    """Get the temperature from OWM"""

    owm = OWM(config.OWM_API_KEY)
    mgr = owm.weather_manager()
    one_call = mgr.one_call(lat=config.LATITUDE, lon=config.LONGITUDE)
    forecasts = one_call.forecast_hourly[:24]

    min_temp = forecasts[0].temperature("celsius")["temp"]
    min_temp_time = forecasts[0].reference_time("date")
    for forecast in forecasts:
        fc_temp = forecast.temperature("celsius")["temp"]
        fc_time = forecast.reference_time("date")
        logger.debug(f"Time: {fc_time}; Temp: {fc_temp}C")
        if fc_temp < min_temp:
            min_temp = fc_temp
            min_temp_time = fc_time

    logger.info(f"Minimum temperature from OWM is {min_temp}C at {min_temp_time}")
    return min_temp, min_temp_time


def get_met_office_temp():

    con = datapoint.connection(api_key=config.DATAPOINT_API_KEY)

    # MET_COORDS is a tuple, so unpack it in the argument
    location = con.get_nearest_forecast_site(config.LATITUDE, config.LONGITUDE)
    forecast = con.get_forecast_for_site(location.id, "3hourly")

    # Only get the next 24 hours of forecasts
    # A check of each timestamp against an end date seems easiest given the
    # structure of datapoint
    tomorrow = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    now = datetime.datetime.now(datetime.timezone.utc)

    min_temp = forecast.days[0].timesteps[0].temperature.value
    # Date is stored as a datetime object not an 'element'
    min_temp_time = forecast.days[0].timesteps[0].date

    for day in forecast.days:
        for timestep in day.timesteps:
            if timestep.date < tomorrow and timestep.date > now:
                temp = timestep.temperature.value
                time = timestep.date
                logger.debug(f"Time: {time}; Temp: {temp}C")
                if timestep.temperature.value < min_temp:
                    min_temp = temp
                    min_temp_time = time

    logger.info(f"Minimum temperature from Met Office is {min_temp}C at {min_temp_time}")
    return min_temp, min_temp_time


def send_email(owm_min, owm_min_time, met_min, met_min_time):
    """Send an email to me, telling me if there will be a frost"""

    # Set up a connection to gmail or somewhere
    smtp_con = smtplib.SMTP_SSL(host=config.MAIL_HOST, port=config.MAIL_PORT)
    smtp_con.login(config.MAIL_USER, config.MAIL_PASSWD)

    # Build a message. Message depends on the forecasts.
    msg = EmailMessage()
    msg["From"] = config.MAIL_FROM
    msg["to"] = config.MAIL_TO
    msg["Subject"] = "Frost alert!"

    message_text = build_message(owm_min, owm_min_time, met_min, met_min_time)

    msg.set_content(message_text)

    # Send the message
    smtp_con.send_message(msg)


def build_message(owm_min, owm_min_time, met_min, met_min_time):
    """Assemble the text to send as a message"""

    owm_time = owm_min_time.strftime("%H:%M on %Y-%m-%d")
    met_time = met_min_time.strftime("%H:%M on %Y-%m-%d")

    if owm_min <= 3 and met_min <= 3:
        predicted_by = "OWM and the Met Office"
    elif owm_min <= 3 and met_min > 3:
        predicted_by = "OWM"
    elif owm_min > 3 and met_min <= 3:
        predicted_by = "the Met Office"
    else:
        predicted_by = "nobody"

    logger.info(f"Frost predicted by {predicted_by}")
    message = """\
Alert! Frost is predicted by {} tonight!

OpenWeatherMap predicts a minimum of {}C at {}.
The Met Office predicts a minimum of {}C at {}.

    """.format(
        predicted_by, owm_min, owm_time, met_min, met_time
    )

    return message


def main():

    # Get the weather forecast from both things
    owm_min, owm_min_time = get_owm_temp()
    met_min, met_min_time = get_met_office_temp()

    if owm_min <= 3 or met_min <= 3:
        send_email(owm_min, owm_min_time, met_min, met_min_time)


if __name__ == "__main__":
    main()
