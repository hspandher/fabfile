import unittest
from fabric.api import local, settings

from ..deploy import Deployment


class TestCleanCodeRepositoryMixin(object):

    def setUp(self):
        if not hasattr(self, 'code_directory'):
            raise AttributeError("Any class that means to inherit {0} should define `code_directory` variable.")

        with settings(warn_only = True):
            local('rm -R {0}'.format(self.code_directory))


class TestDeployment(TestCleanCodeRepositoryMixin, unittest.TestCase):

    code_directory = 'tests/test_deploy/shine'

    def setUp(self):
        super(TestDeployment, self).setUp()

        self.origin_url = 'https://sample_git_url/'
        self.code_directory = 'tests/test_deploy/shine'

        self.deployment = Deployment(scm_url = self.origin_url, code_directory = self.code_directory)

    def test_does_local_repo_exists_return_false_if_repo_does_not_exists(self):
        self.assertFalse(self.deployment.does_local_repo_exists())

    def test_does_local_repo_exists_return_true_if_repo_exists(self):
        local('mkdir -p {0}'.format(self.code_directory))

        self.assertTrue(self.deployment.does_local_repo_exists())
