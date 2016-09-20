from redmine import Redmine
from configuration import config

from extras import send_mail
from . import exceptions

class RedmineAccount:

    REDMINE_HOST = config.REDMINE_HOST
    REDMINE_KEY = config.REDMINE_KEY

    def __init__(self, api_key, issue_id):
        self.api_key
        self.issue_id = issue_id

        self._redmine = Redmine(self.REDMINE_HOST, key = self.REDMINE_KEY)



class DeploymentStatusHandler:

    SUCCESS_SUBJECT = "Deployment Successful"
    FAILURE_SUBJECT = "Deployment Failure"

    REDMINE_HOST = config.REDMINE_HOST
    REDMINE_KEY = config.REDMINE_KEY

    def __init__(self, issue_id, old_assignee_email, new_assignee_email, success_message = 'Deployment Successful'):
        self.issue_id = issue_id
        self.old_assignee_email = old_assignee_email
        self.new_assignee_email = new_assignee_email
        self.success_message = success_message

        self.redmine = Redmine(self.REDMINE_HOST, key = self.REDMINE_KEY)

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        if isinstance(value, exceptions.GitFailureException):
            update_data = {
                'status_id': config.REDMINE_STATUS_MAPPING['new'],
                'assigned_to_id': self.redmine.user.filter(name = self.old_assignee_email)[0].id
            }

            mail_data = (self.old_assignee_email, self.FAILURE_SUBJECT, value.detail)
        else:
            update_data = {
                'assigned_to_id': self.redmine.user.filter(name = self.new_assignee_email)[0].id
            }
            mail_data = (self.old_assignee_email, self.SUCCESS_SUBJECT, self.success_message)

        self.redmine.issue.update(self.issue_id, **update_data)
        send_mail(*mail_data)

