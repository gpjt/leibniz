import os
import shutil
import subprocess
import tempfile
import time
from unittest import TestCase


DEFAULT_WAIT_FOR_TIMEOUT = 10



class FunctionalTest(TestCase):

    def setUp(self):
        self.working_dir = tempfile.mkdtemp()


    def tearDown(self):
        shutil.rmtree(self.working_dir)


    def run_and_fail_on_error(self, command):
        return_code = subprocess.call(command, shell=True)
        if return_code:
            self.fail("Error running bash command")


    def wait_for(self, condition_function, message_fn_or_str, timeout_seconds=DEFAULT_WAIT_FOR_TIMEOUT, allow_exceptions=False):
        time_between = min(timeout_seconds / 10.0, 5)
        start = time.time()
        end = start + timeout_seconds
        exception_raised = False
        tries = 0
        while tries < 2 or time.time() < end:
            try:
                tries += 1
                if condition_function():
                    return
                exception_raised = False
            except:
                if not allow_exceptions:
                    raise
                exception_raised = True
            time.sleep(time_between)
        if exception_raised:
            raise
        if isinstance(message_fn_or_str, basestring):
            message = message_fn_or_str
        else:
            message = message_fn_or_str()
        self.fail("Timeout waiting for condition: %s" % (message,))


    def readAll(self, filename):
        with open(filename, "r") as f:
            contents = ""
            while True:
                data = f.read()
                if not data:
                    break
                contents += data
        return contents


    def wait_for_file_to_have_contents(self, expected_contents, filename):
        def file_to_have_contents():
            if not os.path.exists(filename):
                return False
            return expected_contents == self.readAll(filename)
        self.wait_for(
            file_to_have_contents,
            "File %s to have contents %s (contents were %s)" % (filename, expected_contents, self.readAll(filename))
        )

