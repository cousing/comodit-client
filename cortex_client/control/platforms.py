# control.applications - Controller for cortex Applications resources.
# coding: utf-8
#
# Copyright 2010 Guardis SPRL, Liège, Belgium.
# Authors: Laurent Eschenauer <laurent.eschenauer@guardis.com>
#
# This software cannot be used and/or distributed without prior
# authorization from Guardis.

from cortex_client.control.organization_resource import OrganizationResourceController

class PlatformsController(OrganizationResourceController):

    _template = "platform.json"

    def __init__(self):
        super(PlatformsController, self).__init__()

    def _get_collection(self, org):
        return org.platforms()

    def _help(self, argv):
        print '''You must provide an action to perform on this resource.

Actions:
    list <org_name>                 List all platforms of a given organization
    show <org_name> <plat_name>     Show the details of a platform
    add <org_name>                  Add a platform
    update <org_name> <plat_name>   Update a platform
    delete <org_name> <plat_name>   Delete a platform
'''