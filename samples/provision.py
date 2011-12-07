#==============================================================================
# This file illustrates the use of Python API to handle cortex entities.
# Definitions section (after imports) provides the description of several
# entities this script will create (it may need to be updated).
# Script section (after definitions) contains the actual operations (entities
# creation, host provisioning, shutdown and entities removal).
#==============================================================================

# Setup Python path
import sys
sys.path.append("..")


#==============================================================================
# Imports section

import time

from cortex_client.api.api import CortexApi

from definitions import *


#==============================================================================
# Script

def provision_host():
    # API from server cortex listening on port 8000 of localhost is used
    # Username "admin" and password "secret" are used for authentification
    api = CortexApi(comodit_url, comodit_user, comodit_pass)

    host = api.organizations().get_resource(org_name).environments().get_resource(env_name).hosts().get_resource(host_name)


    #############
    # Provision #
    #############

    print "="*80
    print "Provisioning host " + host_name
    host.provision()
    host.update()

    print "="*80
    print "Waiting for the end of installation..."
    while host.get_instance().get_state() == "RUNNING":
        time.sleep(3)

    print "="*80
    print "Restarting..."
    host.start()
    host.update()
    while host.get_state() == "PROVISIONING":
        time.sleep(3)
        host.update()

    print "Host provisioned and running."

#==============================================================================
# Entry point
if __name__ == "__main__":
    provision_host()
