'''
Created on Nov 22, 2010

@author: eschenal
'''
from util import globals
from control.DefaultController import DefaultController, ControllerException
from rest.Client import Client
import json
from control.Exceptions import NotFoundException, MissingException
from pprint import pprint

class HostApplicationsController(DefaultController):

    _resource = "hosts"

    def __init__(self):
        super(HostApplicationsController, self ).__init__()
        self._register(["list"], self._list)
        self._register(["show"], self._show)        
        self._register(["add"], self._add)
        self._register(["update"], self._update)
        self._register(["remove"], self._remove)
        self._default_action = self._list
    
    def _list(self, argv):
        options = globals.options
    
        # Validate input parameters
        if options.uuid:
            uuid = options.uuid
        elif options.path:
            uuid = self._resolv(options.path)
            if not uuid: raise NotFoundException(uuid)
        else:
            raise MissingException("You must provide a valid environment UUID (with --uuid) or path (--path)")
    
        client = Client(self._endpoint(), options.username, options.password)
        result = client.read(self._resource + "/" + uuid + "/applications")
        
        if options.raw:
            print json.dumps(result, sort_keys=True, indent=4)
        else:
            if (result['count'] == "0"):
                print "Request returned 0 object."
            else:
                for o in result['items']:
                    self._render(o)

    def _show(self, argv):
        options = globals.options
    
        # Validate input parameters
        if options.uuid:
            uuid = options.uuid
        elif options.path:
            uuid = self._resolv(options.path)
            if not uuid: raise NotFoundException(uuid)
        else:
            raise MissingException("You must provide a valid environment UUID (with --uuid) or path (--path)")
    
        if (len(argv) == 0):
            print "You must provide the name of the application to delete."
            exit(-1)
        else:
            application = self._resolvApplication(argv[0])
    
        client = Client(self._endpoint(), options.username, options.password)
        result = client.read(self._resource + "/" + uuid + "/applications/" + application)
        
        if options.raw:
            print json.dumps(result, sort_keys=True, indent=4)
        else:
            self._render(result)

    def _add(self, argv):
        options = globals.options
          
        # Validate input parameters
        if options.uuid:
            uuid = options.uuid
        elif options.path:
            uuid = self._resolv(options.path)
            if not uuid: raise NotFoundException(uuid)
        else:
            raise MissingException("You must provide a valid environment UUID (with --uuid) or path (--path)")
          
        if options.filename:
            with open(options.filename, 'r') as f:
                item = json.load(f)
        elif options.json:
            item = json.loads(options.json)
        else:
            raise ControllerException("Adding an application is not possible in interactive mode.")
        
        client = Client(self._endpoint(), options.username, options.password)
        result = client.create(self._resource + "/" + uuid + "/applications/", item)
        
        if options.raw:
            print json.dumps(result, sort_keys=True, indent=4)
        else:
            self._render(result)
            
    def _update(self, argv):
        options = globals.options
          
        # Validate input parameters
        if options.uuid:
            uuid = options.uuid
        elif options.path:
            uuid = self._resolv(options.path)
            if not uuid: raise NotFoundException(uuid)
        else:
            raise MissingException("You must provide a valid environment UUID (with --uuid) or path (--path)")
          
        if options.filename:
            with open(options.filename, 'r') as f:
                item = json.load(f)
        elif options.json:
            item = json.loads(options.json)
        else:
            raise ControllerException("Configuring an application is not possible in interactive mode.")
        
        client = Client(self._endpoint(), options.username, options.password)
        result = client.update(self._resource + "/" + uuid + "/applications/" + item['application'], item)
        
        if options.raw:
            print json.dumps(result, sort_keys=True, indent=4)
        else:
            self._render(result)
        
    def _remove(self, argv):
        options = globals.options
          
        # Validate input parameters
        if options.uuid:
            uuid = options.uuid
        elif options.path:
            uuid = self._resolv(options.path)
            if not uuid: raise NotFoundException(uuid)
        else:
            raise MissingException("You must provide a valid environment UUID (with --uuid) or path (--path)")
          
    
        if (len(argv) == 0):
            print "You must provide the UUID of the application to delete."
            exit(-1)
        else:
            application = self._resolvApplication(argv[0])
        
        client = Client(self._endpoint(), options.username, options.password)
        result = client.delete(self._resource + "/" + uuid + "/applications/" + application)
    
    def _render(self, item, detailed=False):
        app = self._getApplicationDetails(item['application'])    
        print app["name"]
        if item.has_key('settings'):
            for setting in item['settings']:
                print "    %-30s: %s" % (setting['key'], setting['value'])

    def _interactive(self, item=None):
        raise NotImplemented
    
    def _resolv(self, path):
        options = globals.options
        client = Client(self._endpoint(), options.username, options.password)
        result = client.read("directory/organization/" + path)
        if result.has_key('uuid') : return result['uuid']  
        
    def _resolvApplication(self, path):
        options = globals.options
        client = Client(self._endpoint(), options.username, options.password)
        result = client.read("directory/application/" + path)
        if result.has_key('uuid') : return result['uuid']
        
    def _getApplicationDetails(self, uuid):            
        options = globals.options
        client = Client(self._endpoint(), options.username, options.password)
        result = client.read("applications/" + uuid)
        return result
        
    def _endpoint(self):
        options = globals.options
        return options.api