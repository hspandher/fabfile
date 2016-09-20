import contextlib
import fudge
import os
import sys
from fudge import inspector
from redmine import Redmine

from .. import exceptions
from ..testcases import SimpleTestCase
from ..configuration import config
from ..handlers import DeploymentStatusHandler

REDMINE_STATUS_MAPPING = config.REDMINE_STATUS_MAPPING


class RedmineTestCase(SimpleTestCase):

    def _post_teardown(self):
        super()._post_teardown()

        redmine = Redmine(self.REDMINE_HOST, key = self.REDMINE_KEY)

        redmine.project.all().delete()
        redmine.issue.all().delete()
        redmine.user.all()[1:].delete()

@contextlib.contextmanager
def exception_handler(exception):
    try:
        yield
    except exception:
        pass


class TestDeploymentStatusHandler(RedmineTestCase):

    REDMINE_HOST = 'http://localhost:3000'
    REDMINE_KEY = config.REDMINE_KEY

    def setUp(self):
        self.create_redmine_issue()
        self.assignee_email = self.user.mail
        self.success_message = 'Deployment successful'
        self.error_message = 'Conflict while merging'

        self.patch = fudge.patch("{0}.handlers.send_mail".format(config.PROJECT_NAME))
        self.mock_send_mail = self.patch.__enter__()
        self.mock_send_mail.is_callable()

    def tearDown(self):
        self.patch.__exit__(*sys.exc_info())

    def create_redmine_issue(self):
        self.redmine = Redmine(self.REDMINE_HOST, key = self.REDMINE_KEY)

        self.project_data = {
            'name': 'test',
            'identifier': 'test'
        }

        self.project = self.redmine.project.create(**self.project_data)
        self.user = self.redmine.user.all()[0]

        self.user_data = {
            'login': 'user2',
            'firstname': 'user2',
            'lastname': 'user2',
            'mail': 'user2@user.com',
        }

        self.user2 = self.redmine.user.create(**self.user_data)

        self.issue_data = {
            'project_id': self.project.id,
            'subject': 'Temp Issue',
            'status_id': REDMINE_STATUS_MAPPING['resolved'],
            'assigned_to_id': self.user.id
        }

        self.issue = self.redmine.issue.create(**self.issue_data)

        self.issue.status_id = REDMINE_STATUS_MAPPING['resolved'] # in case you are wondering status_id doesn't work in create

        self.issue.save()

        self.redmine.project_membership.create(project_id = self.project.id, user_id = self.user.id, role_ids = [3, 4])
        self.redmine.project_membership.create(project_id = self.project.id, user_id = self.user2.id, role_ids = [3, 4])

    def test_sends_mail_when_deployment_fails(self):
        self.mock_send_mail.expects_call().with_args(self.assignee_email, inspector.arg.any(), inspector.arg.contains(self.error_message)).times_called(1)

        with exception_handler(exceptions.MergeFailedException):
            with DeploymentStatusHandler(issue_id = self.issue.id, old_assignee_email = self.assignee_email, new_assignee_email = self.user2.mail, success_message = '', failure_message = ''):
                raise exceptions.MergeFailedException('staging', 'issue_12345', self.error_message)

    def test_sends_success_mail_when_deployment_is_successful(self):
        self.mock_send_mail.expects_call().with_args(self.assignee_email, DeploymentStatusHandler.SUCCESS_SUBJECT, inspector.arg.contains(self.success_message)).times_called(1)

        with DeploymentStatusHandler(issue_id = self.issue.id, old_assignee_email = self.assignee_email, new_assignee_email = self.user2.mail, success_message = self.success_message, failure_message = ''):
            pass

    def test_reopen_issue_when_deployment_fails(self):
        with exception_handler(exceptions.MergeFailedException):
            with DeploymentStatusHandler(issue_id = self.issue.id, old_assignee_email = self.assignee_email, new_assignee_email = self.user2.mail, success_message = '', failure_message = ''):
                raise exceptions.MergeFailedException('staging', 'issue_12345', self.error_message)

        self.assertEqual(self.redmine.issue.get(self.issue.id).status.id, REDMINE_STATUS_MAPPING['new'])

    def test_keeps_issue_assigned_to_old_assignee_if_deployment_fails(self):
        with exception_handler(exceptions.MergeFailedException):
            with DeploymentStatusHandler(issue_id = self.issue.id, old_assignee_email = self.assignee_email, new_assignee_email = self.user2.mail, success_message = '', failure_message = ''):
                raise exceptions.MergeFailedException('staging', 'issue_12345', self.error_message)

        self.assertEqual(self.redmine.issue.get(self.issue.id).assigned_to.id, self.user.id)

    def test_assigns_issue_to_new_assignee_if_deployment_successful(self):
        with DeploymentStatusHandler(issue_id = self.issue.id, old_assignee_email = self.assignee_email, new_assignee_email = self.user2.mail, success_message = '', failure_message = ''):
            pass

        self.assertEqual(self.redmine.issue.get(self.issue.id).assigned_to.id, self.user2.id)

    def test_assigns_issue_to_old_assignee_if_deployment_fails(self):
        with exception_handler(exceptions.MergeFailedException):
            with DeploymentStatusHandler(issue_id = self.issue.id, old_assignee_email = self.user2.mail, new_assignee_email = self.assignee_email, success_message = '', failure_message = ''):
                raise exceptions.MergeFailedException('staging', 'issue_12345', self.error_message)

        self.assertEqual(self.redmine.issue.get(self.issue.id).assigned_to.id, self.user2.id)
