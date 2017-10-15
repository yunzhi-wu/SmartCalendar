TASK_PRIORITY_HIGH = 3
TASK_PRIORITY_MID  = 2
TASK_PRIORITY_LOW  = 1


class Project:

    def __init__(self, name, priority=TASK_PRIORITY_MID):
        self._name = name
        self._priority = priority

    def show(self):
        print('%s has priority %d' % (self._name, self._priority))

task = Project("Testing")
task.show()