import getpass
import os, sys


def add_to_startup():
    user_name = getpass.getuser()
    # os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    file_name = os.path.abspath(os.path.dirname(sys.argv[0])) + '\FlooPaste.exe'
    # print("exe located in", file_path)
    bat_path = r'C:\Users\%s\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup' % user_name
    bat_path_name = bat_path + '\\' + "FlooPaste.bat"
    if not os.path.exists(bat_path_name):
        with open(bat_path_name, "w+") as bat_file:
            bat_file.write(r'start "" /D "%s" "%s" icon' % (file_path, file_name))


def remove_from_startup():
    user_name = getpass.getuser()
    bat_path = r'C:\Users\%s\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup' % user_name
    bat_path_name = bat_path + '\\' + "FlooPaste.bat"
    if os.path.exists(bat_path_name):
        os.remove(bat_path_name)
