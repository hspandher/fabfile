import sys
import unittest


class SimpleTestCase(unittest.TestCase):

    """
    unittest.TestCase doesn't call `tearDown` method if some exception occurs in
    `setUp`. This prevents necessary cleanup between tests making them dependent
    on each other. To overcome that `SimpleTestCase` uses `_pre_setup` and `_post_teardown`
    methods which would always be called (Well except in some cases like forcefull
    abort by Keyword interrupt etc.)
    """

    def __call__(self, result=None):
        cleanup_successful = self.perform_cleanup(cleanup_method = self._pre_setup)
        if not cleanup_successful:
            return

        super(SimpleTestCase, self).__call__(result)
        self.perform_cleanup(cleanup_method = self._post_teardown)

    def perform_cleanup(self, cleanup_method):
        testMethod = getattr(self, self._testMethodName)
        skipped = (getattr(self.__class__, "__unittest_skip__", False) or
            getattr(testMethod, "__unittest_skip__", False))

        if skipped:
            return True

        try:
            cleanup_method()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            result.addError(self, sys.exc_info())
            return False

        return True

    def _pre_setup(self):
        pass

    def _post_teardown(self):
        pass
