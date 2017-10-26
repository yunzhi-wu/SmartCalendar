# this manager saves all kind of resources, e.g., time
import datetime
from pprint import pprint
from dateutil import parser
import time
import sys
from multiprocessing import Process, Pipe
from event import Event

from debug_print import print_level
from debug_print import debug_level_info
from debug_print import debug_level_debug

from credentials import get_calendar_service

'''
This resource manager is responsible for time
It needs have a resource table.
The resource table is initialized by reading existing calendar,
and is updated by other managers.

This manager will not handle any events, its reading from existing calendar
is just for the resource initialization
'''


class ResourceManager(Process):

    def __init__(self, resource_name='time', if_projects=None):
        Process.__init__(self)
        self._if_projects = if_projects
        self._resource_name = resource_name
        self._month_resource = dict()
        self._existing_events_in_calendar = dict()

        self.init_month_resource()
        self.read_calendar()
        self.update_resource()

    def init_month_resource(self):
        for i in range(-15, 15):
            date = (datetime.date.today() + datetime.timedelta(days=i)).isoformat()
            self._month_resource[date] = list()
            for j in range(0, 48):
                self._month_resource[date].append(list())

    def read_calendar(self):
        service = get_calendar_service()

        now = datetime.datetime.utcnow()
        print('Getting event within one month nearby')
        time_min = (now - datetime.timedelta(days=15)).isoformat() + 'Z'  # 'Z' indicates UTC time
        time_max = (now + datetime.timedelta(days=14)).isoformat() + 'Z'  # 'Z' indicates UTC time
        eventsResult = service.events().list(
            calendarId='primary', timeMin=time_min, timeMax=time_max, singleEvents=True,
            orderBy='startTime').execute()
        self._existing_events_in_calendar = eventsResult.get('items', [])
        print_level(debug_level_debug, "Read {0} events from calendar".
                    format(len(self._existing_events_in_calendar)))

        return

    def update_resource(self):
        for event in self._existing_events_in_calendar:
            start_time_str = event.get("start").get("dateTime")
            end_time_str = event.get("end").get("dateTime")
            start_time = time.strptime(start_time_str[:19], "%Y-%m-%dT%H:%M:%S")
            end_time = time.strptime(end_time_str[:19], "%Y-%m-%dT%H:%M:%S")
            start_day = start_time_str[:10]  # format is like "2017-10-10"
            start_time_slot = int(start_time.tm_hour * 2 + start_time.tm_min / 30)  # 0:30, slot is 1
            end_time_slot = int(end_time.tm_hour * 2 + end_time.tm_min / 30 - 1)  # 1:00, last slot is 1
            for slot in range(start_time_slot, end_time_slot + 1):
                self._month_resource[start_day][slot].append(event)

        return

    def get_timeslot(self, length):
        return

    def set_timeslot(self, period):
        return

    def delete_timeslot(self, period):
        return

    def show_resource(self, week=True, week_offset=0, day=False, day_offset=0):
        today = datetime.date.today()
        if day:
            date_show = today + datetime.timedelta(days=day_offset)
            self.show_resource_day(date_show.isoformat())
        elif week:
            year, week, day = datetime.date.isocalendar(today)
            # todo: support different week offset, now only support current week
            print_level(debug_level_debug, "show resource year {0} week {1}".format(year, week))
            for i in range(1, 8):
                day_offset_in_week = i - day
                date_show = today + datetime.timedelta(days=day_offset_in_week)
                self.show_resource_day(date_show.isoformat())

    def show_resource_day(self, date_str):
        resource = self._month_resource.get(date_str)
        str = date_str + ' '
        for i in range(0, 48):
            if len(resource[i]) == 0:
                str += '_'
            else:
                str += '*'
        print(str)

    def update_project_manager(self):
        if self._if_projects:
            print_level(debug_level_debug, "Sending events_in_calendar_one_month to project manager")
            #  self._if_projects.send(self._existing_events_in_calendar)
            for event in self._existing_events_in_calendar:
                #  print_level(debug_level_debug, "Size of object: {0}".format(sys.getsizeof(event)))
                self._if_projects.send(event)
            print_level(debug_level_debug, "Sending is done")

    def run(self):
        self.update_project_manager()
        while True:
            time.sleep(100)


def print_total_week_hours():
    sleeping = 8 * 7
    work_hours = 8 * 5
    morning_hours = 1 * 7  # breakfast, wash face and rinse mouth
    on_the_way = 1 * 5  # send tong to school
    evening_hours = 1 * 7  # dinner

    basketball = 1.5
    chinese_school = 3
    swimming = 2
    rhythm = 2

    routine_activities = sleeping + work_hours + morning_hours + \
        on_the_way + evening_hours + basketball + chinese_school + \
        swimming + rhythm

    print("Hours in a week, total {0}, routine hours {1}: {2}%".format(24 * 7, routine_activities,
                                                                       int(routine_activities / (24 * 7) * 100)))

    print("Free hours {1}: {2}%".format(24 * 7, 24 * 7 - routine_activities,
                                        int((24 * 7 - routine_activities) / (24 * 7) * 100)))

    daily_family_hours = 1 * 5

    weekend_family_hours = 3 * 2

    house_work_hours = 3

    teaching_chinese = 3

    family_hours = daily_family_hours + weekend_family_hours + house_work_hours + teaching_chinese

    print("Family hours {0}".format(family_hours))

    meet_friends = 4

    english = 10

    swedish = 10

    it = 10

    learning_hours = meet_friends + english + swedish + it

    print("Family hours {0}".format(learning_hours))


def test_resource_manager():
    rm = ResourceManager()
    rm.show_resource_day(datetime.date.today().isoformat())
    rm.show_resource()


if __name__ == '__main__':
    print_total_week_hours()
    test_resource_manager()