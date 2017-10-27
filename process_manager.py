import time
from multiprocessing import Process, Pipe
from project_manager import ProjectManager
from resource_manager import ResourceManager


def launch_processes():
    p1, p2 = Pipe(duplex=True)
    process_project_manager = ProjectManager(if_resource=p1)
    process_resource_manager = ResourceManager(if_projects=p2)

    process_project_manager.start()
    process_resource_manager.start()

    time.sleep(5)

    process_resource_manager.terminate()
    process_project_manager.terminate()


def test_launch_process():
    p1, p2 = Pipe(duplex=True)
    process_project_manager = ProjectManager(if_resource=p1)
    process_resource_manager = ResourceManager(if_projects=p2)

    process_project_manager.start()
    process_resource_manager.start()
    process_resource_manager.show_resource()

    time.sleep(5)

    process_resource_manager.terminate()
    process_project_manager.terminate()


if __name__ == '__main__':
    launch_processes()