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

All the events are read so that this manager knows how much hours are spent on each project.
All the events are saved also.

Each project has a dynamic priority, and provide api for getting the project with
highest priority

What factors decide the priority of a project?
1. Importance and Emergency:
                | very urgent      urgent       not urgent
--------------------------------------------------------
very important  |     900           700           500*
     important  |     800           600           400*
 not important  |     300           200           100

2. Number of hours planned and spent on a project.
The percentage (ratio) of unplanned hours to target hours.
E.g., project has a target hours per week is 10 hours.When 6 hours are planned,priority
is 40; when 10 hours are planned, priority is 0; when 20 hours planned, priority is -100.

When to update the priority of projects?
1. When projects are updated
2. When plans are updated

'''


# todo: save the Project Manager's internal database to a file
# todo: merge the with new configuration file ...
class ProjectManager(Process):
    def __init__(self, project_configure_file='projects.ini', if_resource=None):
        Process.__init__(self)
        self._if_resource = if_resource
        self._project_configure_file = project_configure_file

        '''
        All projects, including projects from configuration, projects saved,
        and project learnt by this tool
        It is a dictionary of dictionary
        '''
        self._projects_names = list()
        self._projects = list()

        '''
        Events in calendar, including saved before, added in calendar manually,
        and scheduled by this tool
        '''
        self._existing_events_in_calendar = list()
        self._existing_events_ids = list()

        self._database_events = "event_database.p"
        self._database_projects = "project_database.p"

        self.get_projects_from_configure_file()
        self.read_database()  # read saved event, saved status of projects

        self.update_project_database_all()

        print_level(debug_level_debug, "Project Manager initialization done")

    def update_project_database_all(self):
        # remove the old database file
        f = open(self._database_projects, 'w')
        f.close()
        for project in self._projects:
            self.update_project_database(project)

    def update_project_database(self, project):
        f = open(self._database_projects, 'ab')
        pickle.dump(project, f)
        f.close()

    @staticmethod
    def read_database_execute(file_name):
        cnt = 0
        output = list()
        database_file = Path(file_name)
        if not database_file.exists():
            return
        f = open(file_name, 'rb')
        while 1:
            try:
                item = pickle.load(f)
                output.append(item)
                cnt += 1
            except EOFError:
                break
        f.close()
        print_level(debug_level_debug, "{0} events read from database file {1}".format(cnt, file_name))
        return output

    def read_database(self):
        read_output = self.read_database_execute(self._database_events)
        if read_output:
            for event in read_output:
                self._existing_events_ids.append(event.get('id'))
                self._existing_events_in_calendar.append(event)

        read_output = self.read_database_execute(self._database_projects)
        if read_output:
            for project in read_output:
                name = project.get('name')
                if name not in self._projects_names:
                    # a project from database, but not exist in configuration
                    self._projects_names.append(project)
                    self._projects.append(project)
                # else:
                    # a project exist both in configure and in database
                    # use the priority from the configuration file

    @staticmethod
    def get_project_priority_by_configure(project):
        importance = project.get('importance')
        emergency = project.get('emergency')
        configure = [importance, emergency]
        if configure == ['3', '3']:
            return 900
        elif configure == ['2', '3']:
            return 800
        elif configure == ['1', '3']:
            return 300
        elif configure == ['3', '2']:
            return 700
        elif configure == ['2', '2']:
            return 600
        elif configure == ['1', '2']:
            return 200
        elif configure == ['3', '1']:
            return 500
        elif configure == ['2', '1']:
            return 400
        elif configure == ['2', '1']:
            return 100
        else:
            return 0

    def get_projects_from_configure_file(self):
        config = configparser.ConfigParser()
        config.read(self._project_configure_file, encoding='utf-8')

        for project_name in config:
            attributes = {key: value for (key, value) in config.items(project_name)}  # setup a dictionary
            project = attributes
            project['name'] = project_name
            project['priority'] = self.get_project_priority_by_configure(project)
            self._projects_names.append(project_name)
            self._projects.append(project)

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
                    f = open(self._database_events, 'ab')
                    pickle.dump(event, f)
                    f.close()

    def check_project_priority(self):
        for project in self._projects:
            importance = project.get('importance')
            emergency = project.get('emergency')
            configure = [importance, emergency]
            if configure == ['3', '3']:
                assert(900 <= project.get('priority') < 1000)
            elif configure == ['2', '3']:
                assert(800 <= project.get('priority') < 900)
            elif configure == ['1', '3']:
                assert(300 <= project.get('priority') < 400)
            elif configure == ['3', '2']:
                assert(700 <= project.get('priority') < 800)
            elif configure == ['2', '2']:
                assert(600 <= project.get('priority') < 700)
            elif configure == ['1', '2']:
                assert(200 <= project.get('priority') < 300)
            elif configure == ['3', '1']:
                assert(500 <= project.get('priority') < 600)
            elif configure == ['2', '1']:
                assert(400 <= project.get('priority') < 500)
            elif configure == ['2', '1']:
                assert(100 <= project.get('priority') < 200)

    def show_project_attributes(self):
        total_hours = 0

        for project in self._projects:
            if project.get('time budget'):
                total_hours += float(project.get('time budget'))

        print_level(debug_level_info, 'Total hours needed per week: {0}'.format(total_hours))

        sorted_projects = []
        max_percentage = 0
        for project in self._projects:
            project_name = project.get('name')
            if project.get('time budget') and project_name:
                time_budget = float(project.get('time budget'))
                time_percentage = int(time_budget / total_hours * 100)
                if max_percentage < time_percentage:
                    max_percentage = time_percentage
                project['time percentage'] = time_percentage
                sorted_projects.append([project_name, project.get('emergency'), project.get('importance')])
        sorted_projects.sort(key=itemgetter(1, 2), reverse=True)
        print_level(debug_level_debug, 'Sorted_projects:')
        print_level(debug_level_debug, sorted_projects)
        print_level(debug_level_debug, '\n')

        for item in sorted_projects:
            project_name = item[0]  # name
            index = self._projects_names.index(project_name)
            project = self._projects[index]
            time_budget = project.get('time budget')
            time_percentage = project.get('time percentage')
            emergency = project.get('emergency')
            importance = project.get('importance')

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
                                    project_name, emergency, importance))


def test_get_project_from_configure_file():
    pm = ProjectManager()
    pm.show_project_attributes()
    pm.check_project_priority()


if __name__ == '__main__':
    test_get_project_from_configure_file()
