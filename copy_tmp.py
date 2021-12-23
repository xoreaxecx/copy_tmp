import argparse
import os
import sys
import time
from distutils.dir_util import copy_tree
from shutil import copy2


FILES_IGNORE = list()
DIRS_IGNORE = dict()


def print_error(error):
    print(f'=============================================================================\n'
          f'{error}\n'
          f'=============================================================================\n')


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
def copy_file(item_path, item_name, store_path, proc, rc):
    global FILES_IGNORE
    done = False
    try:
        copy2(item_path, store_path)
        done = True
    except Exception as e:
        print_error(e)
        if proc:  # attempt to kill a blocking process.
            kill_process(proc)
            try:
                copy2(item_path, store_path)
                done = True
            except Exception as e:
                print_error(e)
        if rc and not done:  # attempt to copy a file with RawCopy.exe.
            os.system(f'{rc} /FileNamePath:"{item_path}" /OutputPath:"{store_path}"')
    if done:
        print(f'file {item_name} copied.')


# attempt to copy a directory.
def copy_dir(item_path, item_name, store_path, nested_count, proc):
    global DIRS_IGNORE
    done = False
    save_path = os.path.join(store_path, item_name)
    try:
        copy_tree(item_path, save_path)
        done = True
    except Exception as e:
        print_error(e)
        if proc:  # attempt to kill a blocking process.
            kill_process(proc)
            try:
                copy_tree(item_path, save_path)
                done = True
            except Exception as e:
                print_error(e)
    if done:
        print(f'dir {item_name} with {nested_count} nested items copied.')


# attempt to kill the specified process.
def kill_process(process_list):
    killed = False
    processes = list(process_list)
    for process in processes:
        response = os.system(f'taskkill /f /im {process}')
        if response == 0:
            print(f'{process} killed.')
            killed = True
            if args.once:
                process_list.remove(process)
        elif response == 1:
            print(f'{process} acces denided.')
        else:
            print(f'{process} not found.')
    if killed:
        time.sleep(2)


# check the input arguments.
def check_args(arguments):
    warnings = []
    # check "-from" dir exists and is directory.
    if not os.path.exists(arguments.path_from):
        warnings.append(f'Cannot access "-from" dir: {arguments.path_from}')
    elif os.path.isfile(arguments.path_from):
        warnings.append(f'Switch "-from" must be a dir, but a file is specified: {arguments.path_from}')
    # check "-to" dir exists and is directory.
    if os.path.isfile(arguments.path_to):
        warnings.append(f'Switch "-to" must be a dir, but a file is specified: {arguments.path_to}')
    elif not os.path.exists(arguments.path_to):
        try:
            os.makedirs(arguments.path_to)
        except Exception as err:
            warnings.append(f'Cannot create "-to" dir: {arguments.path_to}')
            print_error(err)
    # check and set delay.
    if arguments.d < 0:
        warnings.append(f'Invalid value for "-d" switch: {arguments.d}')
    arguments.d = arguments.d / 1000
    # set exclusions.
    arguments.exc = tuple(arguments.exc) if arguments.exc else None
    # check RawCopy arguments.
    if arguments.rc:
        # if rc_path is not specified, set script path + RawCopy.exe.
        if not arguments.rc_path:
            arguments.rc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'RawCopy.exe')
        # check the path specified is a file.
        elif os.path.isdir(arguments.rc_path):
            warnings.append(f'Switch "-rcpath" must be a file, but a dir is specified: {arguments.rc_path}')
        # check RawCopy exists in the specified or script directory.
        if not os.path.exists(arguments.rc_path):
            warnings.append(f'Cannot find RawCopy.exe in the specified path: {arguments.rc_path}')
    else:
        if arguments.rc_path:
            arguments.rc_path = ''
    # show warnings.
    if warnings:
        print('The following invalid switches were used:')
        for w in warnings:
            print(f'\t{w}')
        print("Exiting the program.")
        sys.exit(2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='his name is Robert Paulson.')
    parser.add_argument('-from', dest='path_from', metavar='from\\dir\\path', required=True, type=str, help='path to the dir to catch file.')
    parser.add_argument('-to', dest='path_to', metavar='to\\dir\\path', required=True, type=str, help='path to the dir to store file.')
    parser.add_argument('-checkdirs', action='store_true', help='check dirs and their contents at 1st level.')
    parser.add_argument('-kill', metavar='procname.exe', action='append', type=str, help='if access denied try to kill a process by name. multiple -kill supported.')
    parser.add_argument('-once', action='store_true', help='kills the specified process once without repeating.')
    parser.add_argument('-exc', metavar='extension', action='append', type=str, default=None, help='exclude extension from monitoring. multiple -exc supported.')
    parser.add_argument('-d', metavar='milliseconds', type=int, default=200, help='delay between file checks in milliseconds. 200 is default.')
    parser.add_argument('-rc', action='store_true', help='use RawCopy.exe to copy blocked files.')
    parser.add_argument('-rcpath', dest='rc_path', metavar='path\\to\\RC', type=str, help='path to the RawCopy.exe. "script dir\\RawCopy.exe" is default.')
    args = parser.parse_args()

    check_args(args)
    look_around(args.path_from, args.checkdirs)

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
                    copy_file(path, item, args.path_to, args.kill, args.rc_path)
                    FILES_IGNORE.append(item)
                else:
                    if args.checkdirs:
                        nested = os.listdir(path)
                        if item not in DIRS_IGNORE or DIRS_IGNORE[item] != nested:
                            copy_dir(path, item, args.path_to, len(nested), args.kill)
                            DIRS_IGNORE[item] = nested
                    else:
                        print(f'new dir found: {path}')
                        FILES_IGNORE.append(item)
            items_count = ic
        time.sleep(args.d)
