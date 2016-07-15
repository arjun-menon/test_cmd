test-cmd
========
This is a utility for building functional tests for command-line applications.

Usage
-----
Test cases usually consist of pairs of input and output files, as well as an optional ``tests.json`` file specifying applicable command-line arguments.  The input file is piped in via ``STDIN``. If the command being tested emits the expected output file via ``STDOUT``, the test case passes. A file representing an expected ``STDERR`` output can also optionally be specified.

The input/output file pairs must follow the following naming pattern:::

  test-A.in.txt  ->  test-A.out.txt
  test-B.in.txt  ->  test-B.out.txt, test-B.err.txt
  test-C.in.txt  ->  test-C.out.txt

The file extension (``.txt`` here) can be anything. The file naming pattern is ``*.in*`` for input files, ``*.out*`` for expected output files, and ``*.err*`` for expected error files.

The content of the ``*.in.*`` file is piped to the command being tested, and its ``STDOUT`` is compared against the ``*.out*`` file. If a ``*.err.*`` file has been provided, then the command ``STDERR`` is matched against it as well.

``test-cmd`` takes in two command-line arguments:
 1. The path to the directory containing test cases.
 2. The path to the command being tested.

Command-line arguments for test cases can be specified by creating a special file named 'tests.json', and placing it in the directory containing your test cases. This ``tests.json`` file maps test cases to objects representing command-line arguments for that test case. If a command-line argument is a non-string value (e.g. a complex JavaScript object), the argument is stringified (with Python's ``json.dumps``), and passed in as JSON.
