#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) Arjun G. Menon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import print_function
from json import dumps, loads
from collections import OrderedDict
from subprocess import Popen, PIPE
from sys import stdout, exit, version_info
from os import path, listdir
from multiprocessing import cpu_count
from threading import Thread, Semaphore
from difflib import unified_diff, diff_bytes

max_parallel = Semaphore(cpu_count())

# Black & White
bw = False


class TestCase(Thread):
    def __init__(self, cmd, tests_dir, input_file_name, **kwargs):
        name = self.construct_test_name(input_file_name)
        Thread.__init__(self, name=name)

        self.name = name
        self.cmd = cmd
        self.tests_dir = tests_dir
        self.success = False
        self.details = ''

        self.input_file = path.join(tests_dir, input_file_name)
        self.stdout_file = path.join(tests_dir, self.construct_stdout_file_name(input_file_name))
        self.stderr_file = path.join(tests_dir, self.construct_stderr_file_name(input_file_name))

        self.kwargs = kwargs

    @staticmethod
    def construct_test_name(input_file_name):
        input_file_root, file_ext = path.splitext(input_file_name)
        file_root, in_ext = path.splitext(input_file_root)
        assert in_ext == '.in'

        return file_root.replace('-', ' ')

    @staticmethod
    def get_file_root_and_ext(input_file_name):
        input_file_root, file_ext = path.splitext(input_file_name)
        file_root, in_ext = path.splitext(input_file_root)
        assert in_ext == '.in'
        return file_root, file_ext

    @staticmethod
    def construct_stdout_file_name(input_file_name):
        file_root, file_ext = TestCase.get_file_root_and_ext(input_file_name)
        return file_root + '.out' + file_ext

    @staticmethod
    def construct_stderr_file_name(input_file_name):
        file_root, file_ext = TestCase.get_file_root_and_ext(input_file_name)
        return file_root + '.err' + file_ext

    @staticmethod
    def read_file(file_name):
        with open(file_name) as f:
            content = f.read()
            if version_info.major == 2 and isinstance(content, unicode):
                content = content.decode()
        if version_info.major >= 3:
            content = bytes(content, 'utf-8')
        return content

    def convert_output(self, text):
        if self.kwargs.get("to_unix", False):
            text = text.replace(b"\r\n", b"\n")
        if self.kwargs.get("rtrim", False):
            text = b"\n".join([line.rstrip(b" ") for line in text.split(b"\n")]).rstrip(b"\n")
        return text

    def run_cmd(self, input_text):
        global max_parallel
        stdout = None
        stderr = None
        process = None

        max_parallel.acquire()
        try:

            process = Popen(self.cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate(input=input_text)
        finally:
            max_parallel.release()

        return stdout, stderr, process


    def detail(self, s=''):
        self.details += s + '\n'

    def run(self):
        self.detail(color(self.name, Color.UNDERLINE))
        test_input = self.read_file(self.input_file)
        self.detail(color('Command:', Color.BOLD) + ' ' + ' '.join(self.cmd))
        stdout, stderr, process = self.run_cmd(test_input)
        stdout = self.convert_output(stdout)
        stderr = self.convert_output(stderr)

        stdout_match = False
        stderr_match = False

        if path.isfile(self.stdout_file):
            expected_stdout = self.convert_output(self.read_file(self.stdout_file))
            if expected_stdout == stdout:
                stdout_match = True
            else:
                if self.kwargs.get("diff_mode", False):
                    self.detail(color('STDOUT:', Color.YELLOW))
                    for line in diff_bytes(unified_diff, expected_stdout.split(b'\n'), stdout.split(b'\n'),
                            fromfile=b'Expected STDOUT', tofile=b'Received STDOUT'):
                        print(line)
                else:
                    self.detail(color('Received STDOUT:', Color.YELLOW))
                    self.detail(stdout.decode())
                    self.detail(color('Expected STDOUT:', Color.YELLOW))
                    self.detail(expected_stdout.decode())
        elif len(stdout) > 0:
            self.detail(color('Received STDOUT:', Color.YELLOW))
            self.detail(stdout.decode())
            self.detail(color('Missing STDOUT file: %s' % self.stdout_file, Color.YELLOW))
        else:
            stdout_match = True

        if path.isfile(self.stderr_file):
            expected_stderr = self.convert_output(self.read_file(self.stderr_file))
            if expected_stderr == stderr:
                stderr_match = True
            else:
                if self.kwargs.get("diff_mode", False):
                    self.detail(color('STDERR:', Color.YELLOW))
                    for line in diff_bytes(unified_diff, expected_stderr.split(b'\n'), stderr.split(b'\n'),
                            fromfile=b'Expected STDERR', tofile=b'Received STDERR'):
                        print(line)
                else:
                    self.detail(color('Received STDERR:', Color.YELLOW))
                    self.detail(stderr.decode())
                    self.detail(color('Expected STDERR:', Color.YELLOW))
                    self.detail(expected_stderr.decode())
        elif len(stderr) > 0:
            self.detail(color('Received STDERR:', Color.YELLOW))
            self.detail(stderr.decode())
            self.detail(color('Missing STDERR file: %s' % self.stderr_file, Color.YELLOW))
        else:
            stderr_match = True

        self.success = stdout_match and stderr_match

        if self.success:
            self.detail(color('Success', Color.GREEN))
        else:
            self.detail(color('Failure', Color.RED))


def _decode_list(data): # http://stackoverflow.com/a/6633651/908430
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv

def _decode_dict(data): # http://stackoverflow.com/a/6633651/908430
    rv = {}
    for key, value in data.items():
        if version_info.major == 2 and isinstance(key, unicode):
            key = key.encode('utf-8')
        if version_info.major == 2 and isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv

def is_input_file(name):
    name, first_ext = path.splitext(name)
    name, second_ext = path.splitext(name)

    if second_ext == '.in':
        return True
    return False

def parse_cmdline_args_json(cmdline_args_json):
    cmdline_args = list()

    for arg, val in cmdline_args_json.items():
        cmdline_args.append(arg)
        cmdline_args.append(dumps(val))

    return cmdline_args

def replace_at_sign_with_cmdline_args(case, cmdline_args):
    updated_cmd = list()
    for cmd_segment in case.cmd:
        if cmd_segment == '@':
            updated_cmd.extend(cmdline_args)
        else:
            updated_cmd.append(cmd_segment)
    case.cmd = updated_cmd

def set_cmdline_args_from_tests_json(tests_dir, test_cases):
    tests_json_file = path.join(tests_dir, 'tests.json')
    with open(tests_json_file) as f:
        tests_json = loads(f.read(), object_hook=_decode_dict)

    for name, cmdline_args_json in tests_json.items():
        if name in test_cases.keys():
            case = test_cases[name]

            if isinstance(case, TestCase):
                cmdline_args = parse_cmdline_args_json(cmdline_args_json)
                replace_at_sign_with_cmdline_args(case, cmdline_args)

def clear_at_sign_from_cmd(test_cases):
    for case in test_cases.values():
        try:
            case.cmd.remove('@')
        except ValueError:
            pass

def get_test_cases(cmd, tests_dir, **kwargs):
    file_list = listdir(tests_dir)
    file_names = sorted(filter(lambda name: is_input_file(name), file_list))

    test_cases = OrderedDict()

    for file_name in file_names:
        test_case = TestCase(cmd, tests_dir, file_name, **kwargs)
        test_cases[test_case.name] = test_case

    set_cmdline_args_from_tests_json(tests_dir, test_cases)
    clear_at_sign_from_cmd(test_cases)

    return test_cases

class Color(object):
    # values from: https://github.com/ilovecode1/pyfancy/blob/master/pyfancy.py
    END = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    UNDERLINE = '\033[4m'

def color(text, color):
    if bw:
        return text
    else:
        return '%s%s%s' % (color, text, Color.END)

def test_cmd(tests_dir, cmd, **kwargs):
    test_cases = get_test_cases(cmd, tests_dir, **kwargs)

    print('Running %i tests on %i CPUs...\n' % (len(test_cases), cpu_count()))

    for case in test_cases.values():
        case.start()

    total, passed = len(test_cases), 0
    for case in test_cases.values():
        case.join()
        print(case.details)
        passed += 1 if case.success else 0

    if passed == total:
        print(color('All %d tests passed.' % total, Color.BLUE))
        return True
    else:
        print(color('%d tests passed, %d tests failed.' % (passed, total - passed), Color.BLUE))
        return False

class TestCmdException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

def validate_cmdline_args(tests_dir, cmd):
    if not path.isdir(tests_dir):
        raise TestCmdException("The directory '%s' does not exist." % tests_dir)

    if not path.isfile(cmd[0]):
        raise TestCmdException("The command '%s' does not exist." % cmd[0])

    at_sign_seen = False
    for cmd_segment in cmd:
        if cmd_segment == '@':
            if at_sign_seen:
                raise TestCmdException("Only one '@' command-line args substituion marker allowed.")
            at_sign_seen = True

def main():
    global bw
    import argparse
    parser = argparse.ArgumentParser(description='Functional Testing Utility for Command-Line Applications')
    parser.add_argument('-b', '--bw', dest='bw', action='store_true', default=False, help='black & white output')
    parser.add_argument('-d', '--diff', dest='diff_mode', action='store_true', default=False, help='diff output')
    parser.add_argument('tests_dir', type=str, help='Path to the directory containing test cases')
    parser.add_argument('cmd', type=str, help='Path to the command to be tested')
    parser.add_argument('args', type=str, help="The command-line arguments with an ampersand character '@' marking" +
        "where arguments from test.json should be injected", nargs=argparse.REMAINDER)
    parser.add_argument('-u', '--to-unix', action='store_true', default=False,
        help='convert CR+LF to LF in cmd output and test files')
    parser.add_argument('-t', '--rtrim', action='store_true', default=False,
        help='ignore trailing whitespaces at the end of each line as well as trailing newlines')
    args = parser.parse_args()
    tests_dir = args.tests_dir
    cmd = [args.cmd]
    cmd.extend(args.args)

    bw = args.bw
    diff_mode = args.diff_mode
    kwargs = {
        "to_unix": args.to_unix,
        "rtrim": args.rtrim,
        "diff_mode": args.diff_mode,
    }

    is_a_tty = hasattr(stdout, 'isatty') and stdout.isatty()
    if not bw and not is_a_tty:
        bw = False

    try:
        validate_cmdline_args(tests_dir, cmd)
        exit(0 if test_cmd(tests_dir, cmd, **kwargs) else 1)
    except TestCmdException as ex:
        print(color('test-cmd error: ', Color.RED), ex.message)
        exit(2)

if __name__ == '__main__':
    main()
