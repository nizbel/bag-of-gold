# -*- coding: utf-8 -*-
import time
from unittest.runner import TextTestResult

from django.test.runner import DiscoverRunner

SLOW_TEST_THRESHOLD = 1

class TimeLoggingTestResult(TextTestResult):

    def startTest(self, test):
        self._started_at = time.time()
        super(TimeLoggingTestResult, self).startTest(test)

    def addSuccess(self, test):
        elapsed = time.time() - self._started_at
        if elapsed > SLOW_TEST_THRESHOLD:
            name = self.getDescription(test)
            self.stream.write(
                "\n{} ({:.03}s)\n".format(
                    name, elapsed))
        super(TimeLoggingTestResult, self).addSuccess(test)

class TimeLoggingTestRunner(DiscoverRunner):
    def get_resultclass(self):
        return TimeLoggingTestResult