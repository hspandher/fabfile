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

    def __init__(self, issue_id, assignee_email, success_message = 'Deployment Successful'):
        self.issue_id = issue_id
        self.assignee_email = assignee_email
        self.success_message = success_message

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        if isinstance(value, exceptions.GitFailureException):
            send_mail(self.assignee_email, self.FAILURE_SUBJECT, value.detail)
        else:
            send_mail(self.assignee_email, self.SUCCESS_SUBJECT, self.success_message)

