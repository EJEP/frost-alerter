# Frost Alerter #

A python script to send an email if frost is expected in the next 24 hours at a specified location. Originally intended to warn me to bring in frost tender plants.

## Requirements ##

This program requires API keys for the [OpenWeatherMap API](https://openweathermap.org/api) and the MetOffice [Datapoint API](https://www.metoffice.gov.uk/datapoint). These are accessed in python using the [pyowm](https://github.com/csparpa/pyowm) and [datapoint](https://github.com/ejep/datapoint-python) modules.

The email is sent using `smtplib` and `email`, both part of the python standard library.

## Configuration ##

The configuration is done in `config.py`. A skeleton file is provided. Some of the information in `config.py` is secret, including the password for the email service used.

The variables in `config.py` are:

+ `OWM_API_KEY`: The API key for OpenWeatherMap.
+ `DATAPOINT_API_KEY`: The API key for datapoint.
+ `MAIL_HOST`: The smtp server to connect to.
+ `MAIL_PORT`: The port to use to connect to the smtp server.
+ `MAIL_USER`: The username to use to login to the smtp server.
+ `MAIL_PASSWD`: The password to use to login to the smtp server.
+ `MAIL_TO`: The email address(es) to send the alert to.
+ `MAIL_FROM`: The email address to set in the 'from' field of the email header.
+ `OWM_COORDS`: The coordinates to use for the weather report from OpenWeatherMap.
+ `MET_COORDS`: The coordinates to use for the weather report from datapoint.

## Usage ##

When run, the script will send an email to the specified address(es) if either of the weather services reports a temperature below 3 degrees within the next 24 hours. It could be run every day in `cron` or similar.
