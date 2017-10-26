import configparser
from operator import itemgetter
from multiprocessing import Process
import pickle
import os
from pathlib import Path

from debug_print import print_level
from debug_print import debug_level_info
from debug_print import debug_level_debug

'''
Project manager saves information about project.
It can read project from configuration files,
and in the future, it can judge if an event belongs to an existing project or not.

Each project has a dynamic priority, and provide api for getting the project with
highest priority

All the events are read so that this manager knows how much hours are spent on each project.
All the events are saved also.
'''


# todo: save the Project Manager's internal database to a file
# todo: merge the with new configuration file ...
class ProjectManager(Process):
    def __init__(self, configure_file='projects.ini', if_resource=None):
        Process.__init__(self)
        self._if_resource = if_resource
        self._configure_file = configure_file
        self._configured_projects = None
        self._existing_events_in_calendar = list()
        self._existing_events_ids = list()
        self._database_file = "event_database.p"
        self.read_database()
        print_level(debug_level_debug, "Project Manager initialization done")

    def read_database(self):
        cnt = 0
        database_file = Path(self._database_file)
        if not database_file.exists():
            return
        f = open(self._database_file, 'rb')
        while 1:
            try:
                event = pickle.load(f)
                self._existing_events_ids.append(event.get('id'))
                self._existing_events_in_calendar.append(event)
                cnt += 1
            except EOFError:
                break
        f.close()
        print_level(debug_level_debug, "{0} items read from database file".format(cnt))

    def get_projects_from_configure_file(self):
        config = configparser.ConfigParser()
        config.read(self._configure_file, encoding='utf-8')

        projects_attributes = dict()
        for project in config:
            attributes = {key: value for (key, value) in config.items(project)}  # setup a dictionary
            projects_attributes[project] = attributes

        self._configured_projects = projects_attributes

    def run(self):
        print_level(debug_level_debug, "Project manager is running")
        while True:
            event = self._if_resource.recv()
            if type(event) is dict:
                event_id = event.get("id")
                if event_id not in self._existing_events_ids:
                    self._existing_events_ids.append(event_id)
                    self._existing_events_in_calendar.append(event)
                    print_level(debug_level_debug, "An event is added into database")
                    f = open(self._database_file, 'ab')
                    pickle.dump(event, f)
                    f.close()

    def show_project_attributes(self):
        total_hours = 0

        for project, attributes in self._configured_projects.items():
            if attributes.get('time budget'):
                total_hours += float(attributes.get('time budget'))

        print_level(debug_level_info, 'Total hours needed per week: {0}'.format(total_hours))

        sorted_projects = []
        max_percentage = 0
        for project, attributes in self._configured_projects.items():
            if attributes.get('time budget'):
                time_budget = float(attributes.get('time budget'))
                time_percentage = int(time_budget / total_hours * 100)
                if max_percentage < time_percentage:
                    max_percentage = time_percentage
                attributes['time percentage'] = time_percentage
                sorted_projects.append([project,attributes.get('emergency'), attributes.get('importance')])
        sorted_projects.sort(key=itemgetter(1, 2), reverse=True)
        print_level(debug_level_debug, 'Sorted_projects:')
        print_level(debug_level_debug, sorted_projects)
        print_level(debug_level_debug, '\n')

        for item in sorted_projects:
            project = item[0]
            attributes = self._configured_projects[project]
            time_budget = attributes.get('time budget')
            time_percentage = attributes.get('time percentage')
            emergency = attributes.get('emergency')
            importance = attributes.get('importance')

            if time_percentage:
                tmp = time_percentage / max_percentage
                if tmp < 0.1:
                    prefix = '*         '
                elif tmp < 0.2:
                    prefix = '**        '
                elif tmp < 0.3:
                    prefix = '***       '
                elif tmp < 0.4:
                    prefix = '****      '
                elif tmp < 0.5:
                    prefix = '*****     '
                elif tmp < 0.6:
                    prefix = '******    '
                elif tmp < 0.7:
                    prefix = '*******   '
                elif tmp < 0.8:
                    prefix = '********  '
                elif tmp < 0.9:
                    prefix = '********* '
                else:
                    prefix = '**********'

                print_level(debug_level_info, '{0} {1:02d}% ({2:02d}/{3:02d}) of these time is for: {4} [{5},{6}]'
                            .format(prefix, time_percentage, int(time_budget), int(total_hours),
                                    project, emergency, importance))


def test_get_project_from_configure_file():
    pm = ProjectManager()
    pm.get_projects_from_configure_file()
    pm.show_project_attributes()


if __name__ == '__main__':
    test_get_project_from_configure_file()