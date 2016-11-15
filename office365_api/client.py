# -*- coding: utf-8 -*-
from .backends import DefaultCredentialsBackend
from .services import OutlookService
from .services import CalendarService
from .services import TokenService


class Office365Client(object):
    api_version = 'v1.0'
    credentials_backend = DefaultCredentialsBackend

    def __init__(self, client_id, client_secret, redirect_uri, access_token, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.outlook = OutlookService(self)
        self.calendar = CalendarService(self)
        self.token = TokenService(self)

    def save_credentials(self, *args, **kwargs):
        self.access_token = kwargs.get('access_token')
        self.refresh_token = kwargs.get('refresh_token')
        self.credentials_backend().save(self, **kwargs)
