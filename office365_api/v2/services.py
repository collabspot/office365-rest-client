# -*- coding: utf-8 -*-
import json
import logging
import urlparse
import urllib

import oauth2client.transport

from .exceptions import Office365ClientError
from .exceptions import Office365ServerError


logger = logging.getLogger(__name__)


class BaseService(object):
    base_url = 'https://graph.microsoft.com'
    graph_api_version = 'v1.0'

    def __init__(self, client, prefix):
        self.client = client
        self.prefix = prefix

    def build_url(self, path):
        if path.startswith('/'):
            path = path.lstrip('/')
        return '%s/%s/%s/%s' % (self.base_url, self.graph_api_version, self.prefix, path)

    def execute_request(self, method, path, query_params=None, headers=None, body=None,
                        parse_json_result=True):
        """
        path: the path of the api endpoint with leading slash (excluding the api version and user id prefix)
        query_params: dict to be urlencoded and appended to the final url
        headers: dict
        body: bytestring to be used as request body

        Returns the parsed JSON data of the response content if the request was successful.
        """
        full_url = self.build_url(path)
        if query_params:
            querystring = urllib.urlencode(query_params)
            full_url += '?' + querystring

        default_headers = {
            'Content-Type': 'application/json'
        }
        if headers:
            default_headers.update(headers)
        resp, content = oauth2client.transport.request(self.client.http,
                                                       full_url,
                                                       method=method.upper(),
                                                       body=body,
                                                       headers=default_headers)
        if resp.status < 300:
            if content:
                return json.loads(content)
        else:
            try:
                error_data = json.loads(content)
            except ValueError:
                # server failed to returned valid json
                # probably a critical error on the server happened
                print content
                raise Office365ServerError(resp.status, content)
            else:
                print error_data
                raise Office365ClientError(resp.status, error_data)


class ServicesCollection(object):
    """
    Wrap a collection of services in a context.
    """
    def __init__(self, client, prefix):
        self.client = client
        self.prefix = prefix

        self.calendar = CalendarService(self.client, self.prefix)
        self.event = EventService(self.client, self.prefix)


class BaseFactory(object):
    def __init__(self, client):
        self.client = client


class UserServicesFactory(BaseFactory):
    def __call__(self, user_id):
        self.user_id = user_id
        if user_id == 'me':
            # special case for 'me'
            return ServicesCollection(self.client, 'me')
        else:
            return ServicesCollection(self.client, 'users/' + user_id)


class CalendarService(BaseService):
    def list(self):
        """ https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/user_list_calendars """
        # TODO: handle pagination
        path = '/calendars'
        method = 'get'
        return self.execute_request(method, path)

    def get(self, calendar_id=None):
        """ https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/calendar_get """
        if calendar_id:
            path = '/calendars/' + calendar_id
        else:
            path = '/calendar'
        method = 'get'
        return self.execute_request(method, path)

    def create(self, **kwargs):
        """ https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/user_post_calendars """
        path = '/calendars'
        method = 'post'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)


class EventService(BaseService):
    def create(self, **kwargs):
        """ https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/user_post_events """
        path = '/events'
        method = 'post'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)


class MessageService(BaseService):
    def list(self, filters=None):
        path = '/messages'
        method = 'get'
        return self.execute_request(method, path, query_params=filters)


class AttachmentService(BaseService):
    def get(self, message_id, attachment_id, filters=None):
        path = '/messages/{}/attachments/{}'.format(message_id, attachment_id)
        method = 'get'
        return self.execute_request(method, path, query_params=filters)