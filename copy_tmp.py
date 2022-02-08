import argparse
import os
import signal
import sys
import time
from distutils.dir_util import copy_tree
from shutil import copy2

FILES_IGNORE = list()
DIRS_IGNORE = dict()


class Log:
    __file = None

    @staticmethod
    def init(to_path):
        log_name = f'__copy_tmp_log_{int(time.time())}.txt'
        Log.__file = open(os.path.join(to_path, log_name), 'a', buffering=1)
        # log arguments
        Log.write(f'{" ".join(sys.argv)}\n-------')

    @staticmethod
    def write(message):
        if Log.__file:
            Log.__file.write(f'{message}\n\n')

    # Close log handle
    @staticmethod
    def close():
        if Log.__file:
            Log.__file.close()


# exit the program with Ctrl + C
def signal_handler(sig, frame):
    Log.close()
    print('-----------------------------------\n'
          'KeyboardInterrupt.\n'
          'Exiting the program.\n'
          '-----------------------------------\n')
    sys.exit(1)


def print_error(error):
    msg = (f'=============================================================================\n'
           f'{error}\n'
           f'=============================================================================\n')
    print(msg)
    Log.write(msg)


def print_message(msg):
    print(msg)
    Log.write(msg)


# capture the contents of the target directory to ignore old files.
def look_around(path_from, checkdirs):
    global FILES_IGNORE, DIRS_IGNORE
    items = os.listdir(path_from)
    if checkdirs:
        for i in items:
            item_path = os.path.join(path_from, i)
            if os.path.isfile(item_path):
                FILES_IGNORE.append(i)
            else:
                nested_items = os.listdir(item_path)
                DIRS_IGNORE[i] = nested_items
    else:
        FILES_IGNORE += items


# calculate the number of files in the directory.
def get_items_count(items, path_from, checkdirs):
    if checkdirs:
        count = 0
        for i in items:
            item_path = os.path.join(path_from, i)
            if os.path.isfile(item_path):
                count += 1
            else:
                nested_items = os.listdir(item_path)
                count += len(nested_items) + 1
    else:
        count = len(items)
    return count


# attempt to copy a file.
def copy_file(item_path, item_name, store_path, proc, rc, kill_once):
    global FILES_IGNORE
    done = False
    try:
        copy2(item_path, store_path)
        done = True
    except Exception as e:
        print_error(e)
        if proc:  # attempt to kill a blocking process.
            kill_process(proc, kill_once)
            try:
                copy2(item_path, store_path)
                done = True
            except Exception as e:
                print_error(e)
        if rc and not done:  # attempt to copy a file with RawCopy.exe.
            command = f'{rc} /FileNamePath:"{item_path}" /OutputPath:"{store_path}"'
            os.system(command)
            print_message(f'Attempt to copy with RawCopy: {command}')
    if done:
        print_message(f'file {item_name} copied.')


# attempt to copy a directory.
def copy_dir(item_path, item_name, store_path, nested_count, proc, kill_once):
    global DIRS_IGNORE
    done = False
    save_path = os.path.join(store_path, item_name)
    try:
        copy_tree(item_path, save_path)
        done = True
    except Exception as e:
        print_error(e)
        if proc:  # attempt to kill a blocking process.
            kill_process(proc, kill_once)
            try:
                copy_tree(item_path, save_path)
                done = True
            except Exception as e:
                print_error(e)
    if done:
        print_message(f'dir {item_name} with {nested_count} nested items copied.')


# attempt to kill the specified process.
def kill_process(process_list, kill_once):
    killed = False
    processes = list(process_list)
    for process in processes:
        response = os.system(f'taskkill /f /im {process}')
        if response == 0:
            print_message(f'{process} killed.')
            killed = True
            if kill_once:
                process_list.remove(process)
        elif response == 1:
            print_message(f'{process} acces denided.')
        else:
            print_message(f'{process} not found.')
    if killed:
        time.sleep(2)


# check the input arguments.
def check_args(args):
    warnings = []
    # check "-from" dir exists and is directory.
    if not os.path.exists(args.path_from):
        warnings.append(f'Cannot access "-from" dir: {args.path_from}')
    elif os.path.isfile(args.path_from):
        warnings.append(f'Switch "-from" must be a dir, but a file is specified: {args.path_from}')
    # check "-to" dir exists and is directory.
    if os.path.isfile(args.path_to):
        warnings.append(f'Switch "-to" must be a dir, but a file is specified: {args.path_to}')
    elif not os.path.exists(args.path_to):
        try:
            os.makedirs(args.path_to)
        except Exception as err:
            warnings.append(f'Cannot create "-to" dir: {args.path_to}')
            print_error(err)
    # check log option
    if not args.no_log:
        Log.init(args.path_to)
    # check and set delay.
    if args.d < 0:
        warnings.append(f'Invalid value for "-d" switch: {args.d}')
    args.d = args.d / 1000
    # set exclusions.
    args.exc = tuple(args.exc) if args.exc else None
    # check RawCopy arguments.
    if args.rc:
        # if rc_path is not specified, set script path + RawCopy.exe.
        if not args.rc_path:
            args.rc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'RawCopy.exe')
        # check the path specified is a file.
        elif os.path.isdir(args.rc_path):
            warnings.append(f'Switch "-rcpath" must be a file, but a dir is specified: {args.rc_path}')
        # check RawCopy exists in the specified or script directory.
        if not os.path.exists(args.rc_path):
            warnings.append(f'Cannot find RawCopy.exe in the specified path: {args.rc_path}')
    else:
        if args.rc_path:
            args.rc_path = ''
    # show warnings.
    if warnings:
        print('The following invalid switches were used:')
        for w in warnings:
            print(f'\t{w}')
        print("Exiting the program.")
        sys.exit(2)
    # register SIGINT handler
    else:
        signal.signal(signal.SIGINT, signal_handler)
        print('-----------------------------------\n'
              'Press Ctrl + C to exit the program.\n'
              '-----------------------------------\n')


def catch_files(args):
    global FILES_IGNORE, DIRS_IGNORE
    items_count = get_items_count(os.listdir(args.path_from), args.path_from, args.checkdirs)
    while 1:
        tmp_items = os.listdir(args.path_from)
        ic = get_items_count(tmp_items, args.path_from, args.checkdirs)
        if ic != items_count:
            for item in tmp_items:
                if item in FILES_IGNORE:
                    continue
                if args.exc:
                    if item.endswith(args.exc):
                        FILES_IGNORE.append(item)
                        continue
                path = os.path.join(args.path_from, item)
                if os.path.isfile(path):
                    copy_file(path, item, args.path_to, args.kill, args.rc_path, args.once)
                    FILES_IGNORE.append(item)
                else:
                    if args.checkdirs:
                        nested = os.listdir(path)
                        if item not in DIRS_IGNORE or DIRS_IGNORE[item] != nested:
                            copy_dir(path, item, args.path_to, len(nested), args.kill, args.once)
                            DIRS_IGNORE[item] = nested
                    else:
                        print_message(f'new dir found: {path}')
                        FILES_IGNORE.append(item)
            items_count = ic
        time.sleep(args.d)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='his name is Robert Paulson.')
    parser.add_argument('-from', dest='path_from', metavar='from\\dir\\path', required=True, type=str, 
                        help='path to the dir to catch file.')
    parser.add_argument('-to', dest='path_to', metavar='to\\dir\\path', required=True, type=str, 
                        help='path to the dir to store file.')
    parser.add_argument('-checkdirs', action='store_true', 
                        help='check dirs and their contents at 1st level.')
    parser.add_argument('-kill', metavar='procname.exe', action='append', type=str, 
                        help='if access denied try to kill a process by name. multiple -kill supported.')
    parser.add_argument('-once', action='store_true', 
                        help='kills the specified process once without repeating.')
    parser.add_argument('-exc', metavar='extension', action='append', type=str, default=None,
                        help='exclude extension from monitoring. multiple -exc supported.')
    parser.add_argument('-d', metavar='milliseconds', type=int, default=200, 
                        help='delay between file checks in milliseconds. 200 is default.')
    parser.add_argument('-rc', action='store_true', help='use RawCopy.exe to copy blocked files.')
    parser.add_argument('-rcpath', dest='rc_path', metavar='path\\to\\RC', type=str, 
                        help='path to the RawCopy.exe. "script dir\\RawCopy.exe" is default.')
    parser.add_argument('-no-log', dest='no_log', action='store_true', help='do not create log.')
    arguments = parser.parse_args()

    check_args(arguments)
    look_around(arguments.path_from, arguments.checkdirs)
    catch_files(arguments)
