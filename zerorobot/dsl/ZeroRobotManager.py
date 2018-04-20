"""
This module contains a wrapper of the go-raml generated client for ZeroRobot.

Jumpscale provie a factory that return a instance of the class defined in this module
We keep this logic in this repository itself and not jumpscale so we don't spread the code over multiple repositories.
"""

from requests.exceptions import HTTPError

from js9 import j
from zerorobot.git.repo import RepoCheckoutError
from zerorobot.service_collection import (ServiceConflictError,
                                          ServiceNotFoundError, TooManyResults)
from zerorobot.service_proxy import ServiceProxy
from zerorobot.template_collection import (TemplateConflictError,
                                           TemplateNotFoundError)
from zerorobot.template_uid import TemplateUID

logger = j.logger.get('zerorobot')


class ServiceCreateError(Exception):
    """
    Exception raised when service fail to create
    """

    def __init__(self, msg, original_exception):
        super().__init__(msg + (": %s" % original_exception))
        self.original_exception = original_exception


class ServiceUpgradeError(Exception):
    """
    Exception raised when service fail to upgrade
    """

    def __init__(self, msg, original_exception):
        super().__init__(msg + (": %s" % original_exception))
        self.original_exception = original_exception


class ServicesMgr:

    def __init__(self, robot):
        self._robot = robot
        self._client = robot._client

    def _instantiate(self, data):
        if data.guid in j.clients.zrobot.list():
            client = j.clients.zrobot.get(data.guid)
        elif hasattr(data, 'secret') and data.secret:
            # create a zrobot client for this service
            client_data = {
                'url': self._client.config.data['url'],
                'secret_': data.secret,  # TODO handle case where secret is not sets
            }
            client = j.clients.zrobot.get(data.guid, data=client_data, interactive=False, create=True)
        else:
            client = self._client

        srv = ServiceProxy(data.name, data.guid, client)
        srv.template_uid = TemplateUID.parse(data.template)
        return srv

    def _get(self, guid=None):
        service, _ = self._client.api.services.GetService(guid)
        return self._instantiate(service)

    @property
    def names(self):
        """
        Return a dictionnary that contains all the service present on
        the ZeroRobot

        key is the name of the service
        value is a ServiceProxy object
        """
        results = {}
        services, _ = self._client.api.services.listServices()
        for service in services:
            srv = self._instantiate(service)
            results[srv.name] = srv
        return results

    @property
    def guids(self):
        """
        Return a dictionnary that contains all the service present on
        the ZeroRobot

        key is the guid of the service
        value is a ServiceProxy object
        """
        results = {}
        services, _ = self._client.api.services.listServices()
        for service in services:
            srv = self._instantiate(service)
            results[srv.guid] = srv
        return results

    def find(self, **kwargs):
        """
        Find some services based on some filters passed in **kwargs
        """
        results = []
        services, _ = self._client.api.services.listServices(query_params=kwargs)
        for service in services:
            results.append(self._instantiate(service))
        return results

    def exists(self, **kwargs):
        """
        Test if a service exists and filter results from kwargs.
        You can filter on:
        "name", "template_uid", "template_host", "template_account", "template_repo", "template_name", "template_version"
        """
        results = self.find(**kwargs)
        return len(results) > 0

    def get(self, **kwargs):
        """
        return a service service based on the filters in kwargs.
        You can filter on:
        "name", "template_uid", "template_host", "template_account", "template_repo", "template_name", "template_version"
        """
        results = self.find(**kwargs)
        i = len(results)
        if i > 1:
            raise TooManyResults("%d services found" % i)
        elif i <= 0:
            raise ServiceNotFoundError()
        return results[0]

    def create(self, template_uid, service_name=None, data=None):
        """
        Instantiate a service from a template

        :param template_uid: UID of the template to use a base class for the service
        :type template_uid: str
        :param service_name: name of the service, needs to be unique within the robot instance, defaults to None
        :param service_name: str, optional
        :param data: a dictionnary with the data of the service to create, defaults to None
        :param data: dict, optional
        :raises ServiceConflictError: raised when a service with same name already exists
        :raises TemplateConflictError: raised when the template uid specified is not specific enough and the robot cannot decide which template to use
        :raises TemplateNotFoundError: raise when the template specified is not found
        :raises ServiceCreateError: raise when an error happens during service creation
        :return: service proxy
        :rtype: ServiceProxy
        """
        req = {
            "template": str(template_uid),
            "version": "0.0.1",
        }
        if service_name:
            req["name"] = service_name
        if data:
            req["data"] = data

        try:
            new_service, resp = self._client.api.services.createService(req)
        except HTTPError as err:
            jsonerr = err.response.json()
            msg = jsonerr['message']
            code = jsonerr['code']
            if err.response.status_code == 409:
                if code == 409:
                    raise ServiceConflictError(msg, None)
                if code == 4090:
                    raise TemplateConflictError(msg)
            elif err.response.status_code == 404:
                raise TemplateNotFoundError(msg)

            e = err.response.json()
            logger.error('fail to create service: %s' % e['message'])
            raise ServiceCreateError(e['message'], err)

        return self._instantiate(new_service)

    def find_or_create(self, template_uid, service_name, data):
        """
        Helper method that first check if a service exists and if not then creates it
        if the service is found, it is returned
        if the service is not found, it is created using the data passed then returned

        @param template_uid: UID of the template of the service
        @param service: the name of the service.
        @param data: a dictionnary with the data of the service if and only if the service is created
                    so if the service already exists, the data argument is not used
        """
        try:
            return self.get(template_uid=template_uid, name=service_name)
        except ServiceNotFoundError:
            return self.create(template_uid=template_uid, service_name=service_name, data=data)


class TemplatesMgr:

    def __init__(self, robot):
        self._robot = robot
        self._client = robot._client

    def add_repo(self, url, branch='master'):
        """
        Add a new template repository
        """
        data = {
            "url": url,
            "branch": branch,
        }
        repo, _ = self._client.api.templates.AddTemplateRepo(data)
        return repo

    def checkout_repo(self, url, revision='master'):
        """
        Checkout a branch/tag/revision of a template repository

        @param url: url of the template repo
        @param revision: branch, tag or revision to checkout
        """
        data = {
            "url": url,
            "branch": revision,
        }
        try:
            self._client.api.templates.CheckoutVersionTemplateRepo(data)
        except HTTPError as err:
            e = err.response.json()
            raise RepoCheckoutError(e['message'], err)

    @property
    def uids(self):
        """
        Returns a list of template UID present on the ZeroRobot
        """
        templates, _ = self._client.api.templates.ListTemplates()
        return {TemplateUID.parse(t.uid): t for t in templates}


class ZeroRobotManager:

    def __init__(self, instance='main'):
        self._client = j.clients.zrobot.get(instance)
        self.services = ServicesMgr(self)
        self.templates = TemplatesMgr(self)
