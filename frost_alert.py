"""Email me when there will be a frost. This happens if the temperature is less
than 3 degrees. Not strictly true but good enough."""

import datetime
import smtplib
from email.message import EmailMessage
import pyowm
from pyowm.alertapi30.enums import WeatherParametersEnum, OperatorsEnum, AlertChannelsEnum
from pyowm.alertapi30.condition import Condition
import datapoint
import config

def get_owm_temp():
    """Get the temperature from OWM"""

    # See https://pyowm.readthedocs.io/en/latest/alerts-api-usage-examples.html
    # for how this works
    # I don't think that triggers are what I want to do...
    owm = pyowm.OWM(config.OWM_API_KEY)

    # OWM_COORDS is a tuple so unpack
    fcst = owm.three_hours_forecast_at_coords(*config.OWM_COORDS)

    most_cold = fcst.most_cold()

    min_temp = most_cold.get_temperature()['temp']

    min_temp_c = min_temp - 273

    #print(min_temp_c)

    # Only want to check the weather for 'tonight'
    cast = fcst.get_forecast()

    # How much we keep depends on how long we run...
    # Keep 24 hours for now, so 8 forecasts
    # Put them in a list for slicing...
    weathers = cast.get_weathers()[:8]

    min_temp_today = weathers[0].get_temperature('celsius')['temp']

    for weather in weathers:
        weather_min_temp = weather.get_temperature('celsius')['temp']
        if weather_min_temp < min_temp_today:
            min_temp_today = weather_min_temp
            min_temp_weather = weather

    #print(min_temp_today)
    #print(type(min_temp_weather.get_reference_time('iso')))
    #print(type(min_temp_weather.get_reference_time('date')))
    #print(min_temp_weather.get_reference_time('date'))

    return min_temp_today, min_temp_weather.get_reference_time('date')

def get_met_office_temp():

    con = datapoint.connection(api_key=config.DATAPOINT_API_KEY)

    # MET_COORDS is a tuple, so unpack it in the argument
    location = con.get_nearest_site(*config.MET_COORDS)
    forecast = con.get_forecast_for_site(location.id, '3hourly')

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
                if timestep.temperature.value < min_temp:
                    min_temp = timestep.temperature.value
                    min_temp_time = timestep.date

    return min_temp, min_temp_time

def send_email(owm_min, owm_min_time, met_min, met_min_time):
    """Send an email to me, telling me if there will be a frost"""

    # Set up a connection to gmail or somewhere
    s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
    s.login(config.MAIL_USER, config.MAIL_PASSWD)

    # Build a message. Message depends on temperature?
    msg = EmailMessage()
    msg['From'] = config.MAIL_FROM
    msg['to'] = config.MAIL_TO
    msg['Subject'] = 'Frost alert!'

    message_text = build_message(owm_min, owm_min_time, met_min, met_min_time)

    msg.set_content(message_text)

    #print(message_text)
    # Send the message
    s.send_message(msg)

def build_message(owm_min, owm_min_time, met_min, met_min_time):
    """Assemble the text to send as a message"""

    owm_time = owm_min_time.strftime('%H:%M on %Y-%m-%d')
    met_time = met_min_time.strftime('%H:%M on %Y-%m-%d')

    if owm_min <= 3 and met_min <= 3:
        predicted_by = 'OWM and the Met Office'
    elif owm_min <= 3 and met_min > 3:
        predicted_by = 'OWM'
    elif owm_min > 3 and met_min <= 3:
        predicted_by = 'the Met Office'
    else:
        predicted_by = 'nobody'

    message = """\
Alert! Frost is predicted by {} tonight!

OpenWeatherMap predicts a minimum of {}C at {}.
The Met Office predicts a minimum of {}C at {}.

    """.format(predicted_by, owm_min, owm_time, met_min, met_time)

    return message

def main():

    # Get the weather forecast from both things
    owm_min, owm_min_time = get_owm_temp()
    met_min, met_min_time = get_met_office_temp()

    #print(owm_min)
    #print(owm_min_time)
    #print(met_min)
    #print(met_min_time)

    if owm_min <= 10 or met_min <= 10:
        send_email(owm_min, owm_min_time, met_min, met_min_time)

if __name__ == "__main__":
    main()



