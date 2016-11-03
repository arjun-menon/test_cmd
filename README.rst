test_cmd
========
This is a tool for black-box testing command-line programs simply based on STDIN, STDOUT, and STDERR.

Tutorial
--------
Test cases usually consist of pairs of input and output files, as well as an optional ``tests.json`` file specifying applicable command-line arguments.  The input file is piped in via ``STDIN``. If the command being tested emits the expected output file via ``STDOUT``, the test case passes. A file representing an expected ``STDERR`` output can also optionally be specified.

The input/output file pairs must follow this naming pattern::

  test-A.in.txt  ->  test-A.out.txt
  test-B.in.txt  ->  test-B.out.txt, test-B.err.txt
  test-C.in.txt  ->  test-C.out.txt

The file extension (``.txt`` here) can be anything. The file naming pattern is ``*.in*`` for input files, ``*.out*`` for expected output files, and ``*.err*`` for expected error files. The content of the ``*.in.*`` file is piped to the command being tested, and its ``STDOUT`` is compared against the ``*.out*`` file. If a ``*.err.*`` file has been provided, then the command ``STDERR`` is matched against it as well.

For an example of test_cmd in action, see the `pypage project <https://github.com/arjun-menon/pypage>`_, particularly its `tests folder <https://github.com/arjun-menon/pypage/tree/master/tests>`_.

Usage
*****
::

    usage: test_cmd.py [-h] tests_dir cmd ...

    Functional Testing Utility for Command-Line Applications

    positional arguments:
      tests_dir   Path to the directory containing test cases
      cmd         Path to the command to be tested
      args        The command-line arguments with an ampersand character '@'
                  markingwhere arguments from test.json should be injected

    optional arguments:
      -h, --help  show this help message and exit

Command-line arguments for test cases can be specified by creating a special file named ``tests.json``, and placing it in the directory containing your test cases. This ``tests.json`` file maps test cases to objects representing command-line arguments for that test case. If a command-line argument is a non-string value (e.g. a complex JavaScript object), the argument is stringified (with Python's ``json.dumps``), and passed in as JSON.
