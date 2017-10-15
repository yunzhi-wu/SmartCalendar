import configparser

from event import Event

import copy

import datetime
from operator import itemgetter



try:
    import argparse
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    parser.add_argument("-i", "--info", action="store_true",
                        help="print basic information")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="display debug information")
    parser.add_argument("-s", "--statistic", action="store_true",
                        help="display projects and their attributes")
    flags = parser.parse_args()
    if flags.info:
        debug_level = debug_level_info
    if flags.verbose:
        debug_level = debug_level_verbose
    elif flags.debug:
        debug_level = debug_level_debug
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'auth\client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

def get_available_week_hours():
    """
    24 hours a day:
    sleeping: 8 hours
    in office: 8.5 hours
    way to and from office: 2 hours
    breakfast: 0.5 hours
    dinner: 1 hours

    Returns:

    """
    work_day_hours = 24 - 8.5 - 8 - 2 - 0.5 - 1
    weekend_day_hours = 24 - 8 - 0.5 - 1 - 1
    week_hours = work_day_hours * 5 + weekend_day_hours * 2

    print_level(debug_level_info, 'work_day_hours: {0} weekend_day_hours = {1}'
                .format(work_day_hours, weekend_day_hours))
    print_level(debug_level_info, 'week_hours: {0}'
                .format(week_hours))
    return week_hours


def create_event(service, events):
    for event in events:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print('Event created: {0}'.format(event.get('htmlLink')))


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
            print("There is a period longer than 6 hours: {0}  -  {1} : {2}"
                  .format(event['start'].get('dateTime'),
                          event['end'].get('dateTime'),
                          event['summary']))
            want_to_ignore = input("Do you want to ignore it? [Yes] ")
            if want_to_ignore in ['', 'y', 'Y', 'yes', 'Yes', 'YES']:
                print("This event is ignored when to assign tasks")
                continue
        used_periods.append([d1, d2])
    print_level(debug_level_info, "Used periods:")
    for period in used_periods:
        print_level(debug_level_info, period)

    merged_periods = []
    if used_periods:
        start, end = used_periods[0]
        # merge possible overlapped period
        for start_itr, end_itr in used_periods[1:]:
            if end < start_itr:  # no overlap with the previous period
                merged_periods.append([start, end])
                start, end = start_itr, end_itr
            elif end < end_itr:  # overlap, but the previous one end earlier
                end = end_itr
        merged_periods.append([start, end])
    print_level(debug_level_info, 'Merged periods:')
    for period in merged_periods:
        print_level(debug_level_info, period)

    today = datetime.date.today()
    morning = datetime.time(7,  0, 0, 0)
    evening = datetime.time(22, 0, 0, 0)

    today_start = datetime.datetime.combine(today, morning)
    today_end = datetime.datetime.combine(today, evening)

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

    print_level(debug_level_info, 'Available periods')
    for period in available_periods:
        print_level(debug_level_info, period)
    return available_periods


def get_event(service):
    today = datetime.date.today()
    start = today.strftime('%Y-%m-%dT%H:%M:%S.000000Z')
    tomorrow = today + datetime.timedelta(days=1)
    end = tomorrow.strftime('%Y-%m-%dT%H:%M:%S.000000Z')

    print('Getting the existing events:')
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
            print_level(debug_level_info, "scheduling: selected period: {0}".format(period_assign))

            emergency = 0
            importance = 0
            name = ''
            for project in projects:
                print_level(debug_level_debug, 'Look at project "{0}": scheduled: {1}'
                            .format(project, scheduled_projects[project]))
                if not scheduled_projects[project]:
                    attributes = {key: value for (key, value) in projects.items(project)}  # setup a dictionary

                    emergency_project = int(attributes.get('emergency'))
                    importance_project = int(attributes.get('importance'))

                    print_level(debug_level_debug,
                                'Look at project "{0}": emergency_project: {1}, importance_project: {2}'
                                .format(project, emergency_project, importance_project))

                    if emergency < emergency_project:
                        emergency = emergency_project
                        importance = importance_project
                        name = project
                    elif emergency == emergency_project and importance < importance_project:
                        importance = importance_project
                        name = project

                    print_level(debug_level_debug, 'Updated: emergency: {0}, importance: {1}, name: {2}'
                                .format(emergency, importance, name))

            print_level(debug_level_verbose, 'scheduling: selected project: emergency {0}, importance {1}, {2}'
                        .format(emergency, importance, name))
            print_level(debug_level_debug, '\n')
            scheduled_projects[name] = True

            event = Event()
            event.set_event_information(summary=name,
                                        period=period_assign,
                                        description=projects[name].get('description'))
            events.append(event.get_event())

    print_level(debug_level_debug, events)
    return events









def main():
    """
    Shows basic usage of the Google Calendar API.
    Get the upcoming ten events
    Insert an event
    """
    projects = get_projects()

    for project in projects:
        print_level(debug_level_debug, projects.items(project), project)

    if flags.statistic:
        get_available_week_hours()
        show_project_attributes(projects)
        return

    service = get_service()
    events = get_event(service)

    available_periods = find_available_periods(events)
    # create_event(service)
    projects = get_projects()
    for project in projects:
        print(project, projects.items(project))

    # TODO: merge events and projects into a unified database

    # scheduling
    newly_scheduled_events = scheduling(available_periods, projects)

    create_event(service, newly_scheduled_events)

if __name__ == '__main__':
    main()

