from __future__ import print_function
import httplib2

from apiclient import discovery

import datetime

from credentials import get_credentials
from event import Event


def main():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    event = Event()

    now = datetime.datetime.now()
    start_time = now + datetime.timedelta(0,60)  # begins 60 seconds later
    end_time = now + datetime.timedelta(0,360)  # lasts 300 seconds

    event.set_times([start_time, end_time])
    event.set_summary("Test insert event")
    event.set_description("Created by SmartCalendar :-)")

    event_inserted = service.events().insert(calendarId='primary', body=event.get_event()).execute()

    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time

    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])
        if "Test insert event" in event['summary']:
            print("Insert test pass")
            # delete this test event
            event_id = event['id']
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            return
    print("Insert test failed")


if __name__ == '__main__':
    main()




