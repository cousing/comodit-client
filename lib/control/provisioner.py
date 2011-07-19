# control.provisioner - Controller for cortex Provisioner service.
# coding: utf-8
# 
# Copyright 2010 Guardis SPRL, Liège, Belgium.
# Authors: Laurent Eschenauer <laurent.eschenauer@guardis.com>
#
# This software cannot be used and/or distributed without prior 
# authorization from Guardis.

from util import globals
from control.abstract import AbstractController
from control.exceptions import NotFoundException, MissingException
from rest.client import Client

class ProvisionerController(AbstractController):

    _resource = "provisioner"

    def __init__(self):
        super(ProvisionerController, self ).__init__()
        self._register(["ks", "kickstart"], self._kickstart)
        self._register(["create"], self._provision)
    
    def _kickstart(self, argv):
        options = globals.options
        
        # Require an object as argument
        if len(argv) == 0:
            raise MissingException("You must provide a valid host UUID or path as argument")
    
        # Validate input parameters
        if options.uuid:
            uuid = argv[0]
        else:
            uuid = self._resolv(argv[0])
            if not uuid: raise NotFoundException(uuid)
    
        client = Client(self._endpoint(), options.username, options.password)
        result = client.read(self._resource + "/kickstart.cfg", parameters={"hostId":uuid}, decode=False)
        print result.read()
        

    def _provision(self, argv):
        options = globals.options
        
        # Require an object as argument
        if len(argv) == 0:
            raise MissingException("You must provide a valid host UUID or path as argument")
    
        # Validate input parameters
        if options.uuid:
            uuid = argv[0]
        else:
            uuid = self._resolv(argv[0])
            if not uuid: raise NotFoundException(uuid)
            
        client = Client(self._endpoint(), options.username, options.password)
        result = client.update(self._resource + "/_provision", parameters={"hostId":uuid}, decode=False)
        print result.read()   
        
    def _render(self, item, detailed=False):
        if item.has_key('settings'):
            for setting in item['settings']:
                print "%-30s: %s" % (setting['key'], setting['value'])

    def _interactive(self, item=None):
        raise NotImplemented
    
    def _endpoint(self):
        options = globals.options
        return options.api
    
    def _resolv(self, path):
        options = globals.options
        client = Client(self._endpoint(), options.username, options.password)
        result = client.read("directory/organization/" + path)
        if result.has_key('uuid') : return result['uuid']