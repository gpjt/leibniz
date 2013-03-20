import os

from functionaltest import FunctionalTest


class TestPushToIntegrationMasterWithPassingTestsDeploys(FunctionalTest):

    def test_doesit(self):
        # Harriet creates a working dev and a bare integration environment
        dev_dir = os.path.join(self.working_dir, "dev-dir")
        self.run_and_fail_on_error("mkdir -p %s && cd %s && git init" % (dev_dir, dev_dir))

        integration_dir = os.path.join(self.working_dir, "integration-dir")
        self.run_and_fail_on_error("mkdir -p %s && cd %s && git init --bare" % (integration_dir, integration_dir))

        # She sets up git so that "git push integration" will push to integration.
        self.run_and_fail_on_error("cd %s && git remote add integration %s" % (dev_dir, integration_dir))

        # She applies the leibniz hooks to the integration repo
        to_install_hook_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hooks", "post-update"))
        installed_hook_file = os.path.join(integration_dir, "hooks", "post-update")
        self.run_and_fail_on_error("cp %s %s" % (to_install_hook_file, installed_hook_file))
        self.run_and_fail_on_error("chmod +x %s" % (installed_hook_file,))

        # She makes a change to the dev repo such that it has a file called run_integration_tests, which 
        # is executable, logs some details about the environment it is run with, and exits with a zero error code.
        dev_run_integration_tests = os.path.join(dev_dir, "run_integration_tests")
        run_integration_tests_flag_file = os.path.join(self.working_dir, "integration_tests")
        with open(dev_run_integration_tests, "w") as f:
            f.write("#!/bin/bash\necho git dir is x${GIT_DIR}x > %s\nexit 0\n" % (run_integration_tests_flag_file,))
        self.run_and_fail_on_error("chmod +x %s" % (dev_run_integration_tests,))

        # She also adds a promote_to_live script, which also logs some deta about its environment and parameters to a well-known file
        dev_promote_to_live = os.path.join(dev_dir, "promote_to_live")
        promoted_to_live_flag_file = os.path.join(self.working_dir, "promoted")
        with open(dev_promote_to_live, "w") as f:
            f.write("#!/bin/bash\necho git dir is x${GIT_DIR}x > %s\necho first param is x${1}x >> %s\nexit 0\n" % (
                promoted_to_live_flag_file, promoted_to_live_flag_file
            ))
        self.run_and_fail_on_error("chmod +x %s" % (dev_promote_to_live,))

        # And she adds an error script, which also touches a well-known file.
        dev_handle_integration_error = os.path.join(dev_dir, "handle_integration_error")
        handle_integration_error_flag_file = os.path.join(self.working_dir, "error")
        with open(dev_handle_integration_error, "w") as f:
            f.write("#!/bin/bash\ntouch %s\nexit 0\n" % (handle_integration_error_flag_file,))
        self.run_and_fail_on_error("chmod +x %s" % (dev_handle_integration_error,))

        # She commits it, and pushes it to integration.
        self.run_and_fail_on_error("cd %s && git add run_integration_tests && git add promote_to_live && git add handle_integration_error && git commit -am'First checkin, with integration testing'" % (dev_dir,))
        self.run_and_fail_on_error("cd %s && git push integration master" % (dev_dir,))

        # After a while, the integration tests are run, with the cofrect environment.
        self.wait_for_file_to_have_contents("git dir is xx\n", run_integration_tests_flag_file)
    
        # Shortly thereafter, it is promoted to live.
        self.wait_for_file_to_have_contents("git dir is xx\nfirst param is x%sx\n" % (integration_dir,), promoted_to_live_flag_file)

        # The error script was not run
        self.assertFalse(os.path.exists(handle_integration_error_flag_file))
