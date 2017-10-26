from credentials_tdd import test_credential_calendar
from insert_event_tdd import test_insert_remove_event
from project_manager import test_get_project_from_configure_file
from resource_manager import test_resource_manager
from quick_start_driver import test_drive_read
from process_manager import test_launch_process


def main():
    test_credential_calendar()
    test_insert_remove_event()
    test_get_project_from_configure_file()
    test_resource_manager()
    test_drive_read()
    test_launch_process()


if __name__ == '__main__':
    main()