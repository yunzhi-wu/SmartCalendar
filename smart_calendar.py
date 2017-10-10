import configparser

from project import Project
from event import Event

import datetime


def create_event(service):
    event = {
        'summary': 'Google I/O 2015',
        'location': '800 Howard St., San Francisco, CA 94103',
        'description': 'A chance to hear more about Google\'s developer products.',
            'start': {
                'dateTime': '2015-12-19T19:00:00+01:00',
                'timeZone': 'Europe/Stockholm',
                },
            'end': {
                'dateTime': '2015-12-19T20:00:00+01:00',
                'timeZone': 'Europe/Stockholm',
                },
        'recurrence': [
            'RRULE:FREQ=DAILY;COUNT=2'
            ],
        'attendees': [
            {'email': 'lpage@example.com'},
            {'email': 'sbrin@example.com'},
            ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
                ],
            },
        }

    event = service.events().insert(calendarId='primary', body=event).execute()
    print('Event created: %s'.format(event.get('htmlLink')))


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
    #for project in config.sections():
    #    attributes = config.items(project)
    #    print(attributes)
    #return config.sections()


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
        #print(start, end)
        # merge possible overlapped period
        for start_itr, end_itr in used_periods[1:]:
            #print(start_itr, end_itr)
            if end < start_itr: # no overlap with the previous period
                #print('no overlap with the previous period')
                merged_periods.append([start, end])
                start, end = start_itr, end_itr
            elif end < end_itr: # overlap, but the previous one end earlier
                #print('overlap, but the previous one end earlier, merge these two periods')
                end = end_itr
            else: # overlap, and the current end earlier
                pass #print('overlap, and the current end earlier, merge these two periods')
        merged_periods.append([start, end])
    print('Merged periods:')
    for period in merged_periods:
        print(period)

    today = datetime.date.today()
    morning = datetime.time(7,  0 ,0, 0) #, datetime.timezone('Europe/Stockholm'))
    evening = datetime.time(22, 0 ,0, 0) #, datetime.timezone('Europe/Stockholm'))

    today_start = datetime.datetime.combine(today, morning)
    today_end = datetime.datetime.combine(today, evening)

    print('today: {0}  -  {1}'.format(today_start, today_end))

    start = today_start
    for period in merged_periods:
        #print(period)
        end = period[0]
        if start < end:
            #print('available_periods')
            #print(start, end)
            available_periods.append([start, end])
        else:
            pass
            #print('not available_periods')
            #print(start, end)
        start = period[1]

    if start < today_end:
        end = today_end
        #print('available_periods')
        #print(start, end)
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

    #end =
    print('Getting the upcoming 10 events, now it is {0}, end is {1}'.format(start, end))
    eventsResult = service.events().list(
        calendarId='primary', timeMin=start, timeMax=end, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()

    #print(eventsResult)

    events = eventsResult.get('items', [])

    #task = Task("Testing")
    #task.show()

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
        print(project, projects.items(project))
        scheduled_projects[project] = False

    events = []
    while available_periods:
        period = available_periods[0]
        if period[1] - period[0] > datetime.timedelta(hours=4):
            period[1] = period[0] + datetime.timedelta(hours=4)
            available_periods[0][0] += datetime.timedelta(hours=4)
        else:
            available_periods.pop([0])

        emergency = 0
        importance = 0
        name = ''
        for project in projects:
            if not scheduled_projects[project]:
                attributes = {key: value for (key, value) in projects.items(project)} # setup a dictionary
                emergency_project = attributes.get('emergency')
                importance_project = attributes.get('importance')
                if emergency < emergency_project:
                    emergency = emergency_project
                    name = project
                elif emergency == emergency_project and importance < importance_project:
                    importance = importance_project
                    name = project
        print('{0} is the project selected'.format(name))
        scheduled_projects[name] = True

        event = Event()
        event.set_summary(name)
        event.set_times(period)
        event.set_description(projects[name].get('description'))
        events.append(event.get_event())

    return events


def main():
    """Shows basic usage of the Google Calendar API.
    Get the upcoming ten events
    Insert an event
    """
    service = get_service()
    events = get_event(service)

    available_periods = find_available_periods(events)
    # create_event(service)
    projects = get_projects()
    for project in projects:
        print(project, projects.items(project))

    # TODO: merge events and projects into a unified database

    # scheduling
    scheduling(available_periods, projects)


if __name__ == '__main__':
    main()

