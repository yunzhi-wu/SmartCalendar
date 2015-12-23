from __future__ import print_function
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import configparser

from project import Project
from event import Event


import copy
import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'auth\client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'


def create_event(service, events):
    for event in events:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print('Event created: {0}'.format(event.get('htmlLink')))


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python.json')

    print(credential_path)
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def get_service():
    """
    Creates a Google Calendar API service object
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    return service


def get_projects():
    config = configparser.ConfigParser()
    config.read('projects.ini', encoding='utf-8')
    return config


def find_available_periods(events):
    """
    :param events: this is existing events in the calendar
    :return: periods that have not assigned any event
    """
    available_periods = []
    if not events:
        print("there is no event assigned yet")
        return available_periods

    used_periods = []
    for event in events:
        fmt = '%Y-%m-%dT%H:%M:%S+01:00'
        d1 = datetime.datetime.strptime(event['start'].get('dateTime'), fmt)
        d2 = datetime.datetime.strptime(event['end'].get('dateTime'), fmt)
        if (d2 - d1) > datetime.timedelta(hours=6):
            print("There is a period longer than 6 hours: {0}  -  {1} : {2}".format(event['start'].get('dateTime'),
                                                                                    event['end'].get('dateTime'),
                                                                                    event['summary']))
            want_to_ignore = input("Do you want to ignore it? [Yes] ")
            if want_to_ignore in ['', 'y', 'Y', 'yes', 'Yes', 'YES']:
                print("This event is ignored when to assign tasks")
                continue
        used_periods.append([d1, d2])
    print("Used periods:")
    for period in used_periods:
        print(period)

    if used_periods:
        merged_periods = []
        start, end = used_periods[0]
        # merge possible overlapped period
        for start_itr, end_itr in used_periods[1:]:
            if end < start_itr:  # no overlap with the previous period
                merged_periods.append([start, end])
                start, end = start_itr, end_itr
            elif end < end_itr:  # overlap, but the previous one end earlier
                end = end_itr
        merged_periods.append([start, end])
    print('Merged periods:')
    for period in merged_periods:
        print(period)

    today = datetime.date.today()
    morning = datetime.time(7,  0 ,0, 0)
    evening = datetime.time(22, 0 ,0, 0)

    today_start = datetime.datetime.combine(today, morning)
    today_end = datetime.datetime.combine(today, evening)

    print('today: {0}  -  {1}'.format(today_start, today_end))

    start = today_start
    for period in merged_periods:
        end = period[0]
        if start < end:
            available_periods.append([start, end])
        else:
            pass
        start = period[1]

    if start < today_end:
        end = today_end
        available_periods.append([start, end])

    print('Available periods')
    for period in available_periods:
        print(period)
    return available_periods


def get_event(service):
    today = datetime.date.today()
    start = today.strftime('%Y-%m-%dT%H:%M:%S.000000Z')
    tomorrow = today + datetime.timedelta(days=1)
    end = tomorrow.strftime('%Y-%m-%dT%H:%M:%S.000000Z')

    print('Getting the upcoming 10 events, now it is {0}, end is {1}'.format(start, end))
    event_results = service.events().list(
        calendarId='primary', timeMin=start, timeMax=end, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()

    events = event_results.get('items', [])

    if not events:
        print('No upcoming events found.')

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])

    return events


def scheduling(available_periods, projects):
    """
    :param available_periods: periods that are free during the day
    :param projects: projects that would be scheduled
    :return: list of events in the format specified in event.py
    """
    scheduled_projects = {}
    for project in projects:
        scheduled_projects[project] = False

    events = []
    for period in available_periods:
        # divide period if it is too long
        while period:
            if period[1] - period[0] > datetime.timedelta(hours=2):
                period_assign = [period[0], period[0] + datetime.timedelta(hours=2)]
                period[0] += datetime.timedelta(hours=2)  # new start time
            else:
                period_assign = copy.copy(period)
                period = []
            print("scheduling: selected period: {0}", period_assign)

            emergency = 0
            importance = 0
            name = ''
            for project in projects:
                if not scheduled_projects[project]:
                    attributes = {key: value for (key, value) in projects.items(project)}  # setup a dictionary
                    emergency_project = int(attributes.get('emergency'))
                    importance_project = int(attributes.get('importance'))
                    if emergency < emergency_project:
                        emergency = emergency_project
                        name = project
                    elif emergency == emergency_project and importance < importance_project:
                        importance = importance_project
                        name = project
            print('scheduling: selected project: {0}'.format(name))
            scheduled_projects[name] = True

            event = Event()
            event.set_event_information(summary=name,
                                        period=period_assign,
                                        description=projects[name].get('description'))
            events.append(event.get_event())
    print(events)
    return events


def main():
    """Shows basic usage of the Google Calendar API.

    Get the upcoming ten events
    Insert an event
    """
    service = get_service()
    events = get_event(service)

    available_periods = find_available_periods(events)

    projects = get_projects()
    for project in projects:
        print(project, projects.items(project))

    # TODO: merge events and projects into a unified database

    # scheduling
    newly_scheduled_events = scheduling(available_periods, projects)

    create_event(service, newly_scheduled_events)

if __name__ == '__main__':
    main()

