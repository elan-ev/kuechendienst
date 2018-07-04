#!/bin/env python3.5
"""This script fetches data from a google sheet, forms a message and posts it
to a matrix server"""

import datetime
import time
import json
import argparse
from httplib2 import Http
import requests
from apiclient.discovery import build
from oauth2client import file, client, tools

PATH_CONFIG = "/etc/kuechendienst/config.json"

print("Starting on " + time.strftime("%Y-%m-%d %H:%M"))

PARSER = argparse.ArgumentParser(
    description='Service to post Kuechendienst to Matrix.')
PARSER.add_argument('--config', dest='PATH_CONFIG', action='store',
                    help="Change path where config.json is read from" +
                    "(default: %s)".format(PATH_CONFIG))
ARGS = PARSER.parse_args()
if ARGS.PATH_CONFIG:
    PATH_CONFIG = ARGS.PATH_CONFIG

print("Reading config from " + PATH_CONFIG)
with open(PATH_CONFIG, 'r') as f:
    CONFIG = json.load(f)

SCOPES = "https://www.googleapis.com/auth/spreadsheets.readonly"
STORE = file.Storage(CONFIG['PATH_CREDENTIALS'])
CREDS = STORE.get()
if not CREDS or CREDS.invalid:
    FLOW = client.flow_from_clientsecrets(CONFIG['PATH_SECRET'], SCOPES)
    CREDS = tools.run_flow(FLOW, STORE)
SERVICE = build('sheets', 'v4', http=CREDS.authorize(Http()))

RESULT = SERVICE.spreadsheets().values().get(
    spreadsheetId=CONFIG['SPREADSHEET_ID'],
    range=CONFIG['RANGE_NAME'],
    majorDimension='ROWS').execute()
ENTRIES = RESULT['values'][1:]
print("Reading List. Length: " + str(len(RESULT['values']) - 1))

WEEKNUMBER = datetime.date.today().isocalendar()[1]
print("We are in week number " + str(WEEKNUMBER))

for entry in ENTRIES:
    if int(entry[0]) == WEEKNUMBER:
        person1 = entry[2]
        person2 = entry[3]
        break

MSG = "Küchendienst in der aktuellen Kalenderwoche " + str(WEEKNUMBER) + ":"
if person1 != "":
    MSG = MSG + " " + person1
    if person2 != "":
        MSG = MSG + " und " + person2
else:
    if person2 != "":
        MSG = MSG + " " + person2
    else:
        MSG = MSG + " keiner"

MSG = MSG.encode('utf-8')

RESULT = requests.post(CONFIG['SERVER_MATRIX_BOT'] + CONFIG['MATRIX_ROOM'],
                       data=(MSG))
print("Using encoding: " + str(RESULT.encoding))
print("URL: " + str(RESULT.url))
print("Posting to Matrix: " + RESULT.text)
