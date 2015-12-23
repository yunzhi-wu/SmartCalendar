import datetime


class Event:
    def __init__(self):
        self._event = {
            'summary': 'Please give me a summary',
            'location': '',
            'description': '',
                'start': {
                    'dateTime': '1000-00-00T00:00:00+01:00',
                    'timeZone': 'Europe/Stockholm',
                    },
                'end': {
                    'dateTime': '1000-00-00T01:00:00+01:00',
                    'timeZone': 'Europe/Stockholm',
                    },
            'recurrence': [
                'RRULE:FREQ=DAILY;COUNT=1'
                ],
            'attendees': [
                #{'email': 'lpage@example.com'},
                #{'email': 'sbrin@example.com'},
                ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                    ],
                },
            }

    def get_event(self):
        return self._event

    def set_summary(self, summary):
        self._event['summary'] = summary

    def set_times(self, period):
        start, end = period
        fmt = '%Y-%m-%dT%H:%M:%S+01:00'
        self._event['start']['dateTime'] = datetime.datetime.strftime(start, fmt)
        self._event['end']['dateTime'] = datetime.datetime.strftime(end, fmt)

    def set_description(self, description):
        self._event['description'] = description
