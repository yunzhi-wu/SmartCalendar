# this manager saves all kind of resources, e.g., time
import datetime
from pprint import pprint

from debug_print import print_level
from debug_print import debug_level_info
from debug_print import debug_level_debug


class ResourceManager:

    def __init__(self, resource_name='time'):
        self._resource_name = resource_name
        self._month_resource = dict()

        self.init_month_resource()
        self.read_database()
        self.read_calendar()
        self.update_resource()

    def init_month_resource(self):
        for i in range(-15, 15):
            date = (datetime.date.today() + datetime.timedelta(days=i)).isoformat()
            self._month_resource[date] = list()
            for j in range(0, 48):
                self._month_resource[date].append(list())

    def read_database(self):
        return

    def read_calendar(self):
        return

    def update_resource(self):
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


def main():
    rm = ResourceManager()
    rm.show_resource_day(datetime.date.today().isoformat())
    rm.show_resource()


if __name__ == '__main__':
    main()