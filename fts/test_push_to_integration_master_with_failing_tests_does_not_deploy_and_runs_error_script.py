import os

from functionaltest import FunctionalTest


class TestPushToIntegrationMasterWithFailingTestsDoesNotDeployAndRunsErrorScript(FunctionalTest):

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
        # is executable and exits with a non-zzero error code.
        dev_run_integration_tests = os.path.join(dev_dir, "run_integration_tests")
        with open(dev_run_integration_tests, "w") as f:
            f.write("#!/bin/bash\necho Oh noes!\necho It b0rked.\necho Some standard error stuff 1>&2\nexit 1\n")
        self.run_and_fail_on_error("chmod +x %s" % (dev_run_integration_tests,))

        # She also adds a promote_to_live script, which touches a well-known file
        dev_promote_to_live = os.path.join(dev_dir, "promote_to_live")
        promoted_to_live_flag_file = os.path.join(self.working_dir, "promoted")
        with open(dev_promote_to_live, "w") as f:
            f.write("#!/bin/bash\ntouch %s\nexit 0\n" % (promoted_to_live_flag_file,))
        self.run_and_fail_on_error("chmod +x %s" % (dev_promote_to_live,))

        # And she adds an error script, which writes its input to a well-known file.
        dev_handle_integration_error = os.path.join(dev_dir, "handle_integration_error")
        handle_integration_error_flag_file = os.path.join(self.working_dir, "error")
        with open(dev_handle_integration_error, "w") as f:
            f.write(
                "#!/bin/bash\necho git dir is x${GIT_DIR}x > %s\ncat >> %s\nexit 0\n" % (
                    handle_integration_error_flag_file, handle_integration_error_flag_file,
                )
            )
        self.run_and_fail_on_error("chmod +x %s" % (dev_handle_integration_error,))

        # She commits it, and pushes it to integration.
        self.run_and_fail_on_error("cd %s && pwd && git add run_integration_tests && git add promote_to_live && git add handle_integration_error && git commit -am'First checkin, with integration testing'" % (dev_dir,))
        self.run_and_fail_on_error("cd %s && git push integration master" % (dev_dir,))

        # Shortly thereafter, her error script is executed.
        # It received the standard output of the integration run as its standard input, and had the 
        # expected environment
        self.wait_for_file_to_have_contents("git dir is xx\nOh noes!\nIt b0rked.\nSome standard error stuff\n", handle_integration_error_flag_file)

        # She confirms that it was not promoted to live.
        self.assertFalse(os.path.exists(promoted_to_live_flag_file))

