import fudge
from fudge import inspector
import os
from redmine import Redmine

from .. import exceptions
from ..testcases import SimpleTestCase
from ..configuration import config
from ..handlers import RedmineAccount, DeploymentStatusHandler

REDMINE_STATUS_MAPPINGS = {
    'new': 1,
    'in_progress': 2,
    'resolved': 3,
    'feedback': 4,
    'closed': 5,
    'rejected': 6
}


class RedmineTestCase(SimpleTestCase):

    def _post_teardown(self):
        super()._post_teardown()

        redmine = Redmine(self.REDMINE_HOST, key = self.REDMINE_KEY)

        redmine.project.all().delete()
        redmine.issue.all().delete()
        redmine.user.all()[1:].delete()


class TestRedmineAccount(RedmineTestCase):

    REDMINE_HOST = 'http://localhost:3000'
    REDMINE_KEY = config.REDMINE_KEY

    def setUp(self):
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
            'status_id': REDMINE_STATUS_MAPPINGS['new'],
            'assigned_to_id': self.user.id
        }

        self.issue = self.redmine.issue.create(**self.issue_data)

        self.redmine_account = RedmineAccount(issue_id = self.issue.id)

    # def test_change_issue(self):
    #     self.redmine_account.change_issue(status_id = REDMINE_STATUS_MAPPINGS['resolved'], assigned_to_id = self.user2.id)

    #     changed_issue = self.redmine.issue.get(issue_id = self.issue.id)

    #     self.assertEqual(changed_issue.status_id, REDMINE_STATUS_MAPPINGS['resolved'])
    #     self.assertEqual(changed_issue.assigned_to_id, self.user2.id)


class TestDeploymentStatusHandler(SimpleTestCase):

    def setUp(self):
        self.issue_id = '12345'
        self.assignee_email = 'no-one@someone.com'
        self.assignee_email = 'hspandher@outlook.com'
        self.success_message = 'Deployment successful'

    @fudge.patch("{0}.handlers.send_mail".format(config.PROJECT_NAME))
    def test_sends_mail_when_deployment_fails(self, mock_send_mail):
        error_message = 'Conflict while merging'
        mock_send_mail.expects_call().with_args(self.assignee_email, inspector.arg.any(), inspector.arg.contains(error_message)).times_called(1)

        try:
            with DeploymentStatusHandler(issue_id = self.issue_id, assignee_email = self.assignee_email, success_message = ''):
                raise exceptions.MergeFailedException('staging', 'issue_12345', error_message)
        except exceptions.MergeFailedException:
            pass

    @fudge.patch("{0}.handlers.send_mail".format(config.PROJECT_NAME))
    def test_does_not_send_mail_when_deployment_is_successful(self, mock_send_mail):
        mock_send_mail.expects_call().with_args(self.assignee_email, DeploymentStatusHandler.SUCCESS_SUBJECT, inspector.arg.contains(self.success_message)).times_called(1)

        with DeploymentStatusHandler(issue_id = self.issue_id, assignee_email = self.assignee_email, success_message = self.success_message):
            pass
