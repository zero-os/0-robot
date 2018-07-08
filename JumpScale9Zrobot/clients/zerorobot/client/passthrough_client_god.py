# DO NOT EDIT THIS FILE. This file will be overwritten when re-running go-raml.


class PassThroughClientGod:
    def __init__(self, http_client):
        self._http_client = http_client

    def set_zrobotgod_header(self, val):
        """" Set header ZrobotGod to '<val>'"""
        return self._http_client.set_header('ZrobotGod', val)
