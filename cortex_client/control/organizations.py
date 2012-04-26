# control.organizations - Controller for cortex Organizations resources.
# coding: utf-8
#
# Copyright 2010 Guardis SPRL, Liège, Belgium.
# Authors: Laurent Eschenauer <laurent.eschenauer@guardis.com>
#
# This software cannot be used and/or distributed without prior
# authorization from Guardis.

import os, json

from cortex_client.util import globals
from cortex_client.control.root_resource import RootResourceController
from cortex_client.control.exceptions import ArgumentException, \
    ControllerException
from cortex_client.control.settings import OrganizationSettingsController
from cortex_client.control.groups import GroupsController
from cortex_client.control.doc import ActionDoc
from cortex_client.control.actions import ActionsQueue, UploadContent, \
    UpdateResource, CreateResource, CreateInstance
from cortex_client.api.application import Application
from cortex_client.api.collection import ResourceNotFoundException
from cortex_client.api.distribution import Distribution
from cortex_client.api.organization import Organization
from cortex_client.api.group import Group
from cortex_client.api.environment import Environment
from cortex_client.api.host import Host, Instance
from cortex_client.api.platform import Platform
from cortex_client.api.contexts import ApplicationContext, PlatformContext, \
    DistributionContext
from cortex_client.api import collections
from cortex_client.control.audit import AuditHelper
from cortex_client.api.exporter import Export


class SyncException(ControllerException):
    def __init__(self, msg):
        ControllerException.__init__(self, msg)


class OrganizationsController(RootResourceController):

    _template = "organization.json"

    def __init__(self):
        super(OrganizationsController, self).__init__()
        self._audit = AuditHelper(self, "<res_name>")

        # actions
        self._register(["import"], self._import, self._print_import_completions)
        self._register(["export"], self._export, self._print_export_completions)
        self._register(["reset-secret"], self._reset_secret, self._print_resource_completions)
        self._register(["audit"], self._audit.audit, self._print_resource_completions)

        self._register_action_doc(self._export_doc())
        self._register_action_doc(self._import_doc())
        self._register_action_doc(self._reset_secret_doc())
        self._register_action_doc(self._audit.audit_doc())

        # subcontrollers
        self._register_subcontroller(["settings"], OrganizationSettingsController())
        self._register_subcontroller(["groups"], GroupsController())

        self._doc = "Organizations handling."

    def get_collection(self, argv):
        return self._api.organizations()

    def _prune_json_update(self, json_wrapper):
        super(OrganizationsController, self)._prune_json_update(json_wrapper)
        json_wrapper._del_field("settings")
        json_wrapper._del_field("groups")
        json_wrapper._del_field("environments")

    def _print_group_completions(self, param_num, argv):
        if param_num < 1:
            self._print_resource_completions(param_num, argv)
        elif param_num == 1:
            self._print_identifiers(collections.groups(self._api, argv[0]))

    def _show_group(self, argv):
        if len(argv) != 2:
            raise ArgumentException("This action takes 2 arguments")

        group = collections.groups(self._api, argv[0]).get_resource(argv[1])
        group.show()

    def _add_user(self, argv):
        if len(argv) != 3:
            raise ArgumentException("This action takes 3 arguments")

        group = collections.groups(self._api, argv[0]).get_resource(argv[1])
        group.add_user(argv[2])
        group.commit()

    def _del_user(self, argv):
        if len(argv) != 3:
            raise ArgumentException("This action takes 3 arguments")

        group = collections.groups(self._api, argv[0]).get_resource(argv[1])
        group.remove_user(argv[2])
        group.commit()

    def _reset_secret(self, argv):
        org = self._get_resource(argv)
        org.reset_secret()

    def _reset_secret_doc(self):
        return ActionDoc("reset-secret", self._list_params(), """
        Resets the secret key associated to the organization.""")

    def _audit(self, argv):
        org = self._get_resource(argv)
        logs = org.audit_logs().get_resources()

        # Display the result
        options = globals.options
        if options.raw:
            json.dumps(logs, sort_keys = True, indent = 4)
        else:
            for log in logs:
                print log.get_timestamp(), log.get_message(), "by", log.get_initiator()

    def _audit_doc(self):
        return ActionDoc("audit", self._list_params(), """
        Displays audit log.""")

    # Import/export

    def __set_root_folder(self, argv):
        if len(argv) < 1:
            raise ArgumentException("Wrong number of arguments")

        self._root = argv[0] # By default, use organization name as folder name
        if len(argv) > 1:
            self._root = argv[1]

    def _print_export_completions(self, param_num, argv):
        if param_num == 0:
            self._print_resource_completions(param_num, argv)
        elif param_num == 1:
            self._print_dir_completions()

    def _export(self, argv):
        self._options = globals.options

        self.__set_root_folder(argv)

        org = self._api.organizations().get_resource(argv[0])
        export = Export(globals.options.force)
        export.export_organization(org, self._root)

    def _export_doc(self):
        return ActionDoc("export", "<org_name> [<output_folder>] [--force]", """
        Export organization onto disk. --force option causes existing files to
        be overwritten.""")

    def _print_import_completions(self, param_num, argv):
        if param_num == 0:
            self._print_dir_completions()

    def _import(self, argv):
        """
        Pushes local data to cortex server. Data may include applications,
        distributions, platforms, organizations, environments and hosts.
        Local data are automatically imported if no collision with remote data
        is detected. In case of collision, 'force' option can be used to still
        import data.
        """
        self._options = globals.options

        if len(argv) < 1:
            raise ArgumentException("Wrong number of arguments")
        self._root = argv[0]

        self._actions = ActionsQueue()
        self._import_organization()

        if self._actions.isFastForward():
            print "Fast-forward import"
            self._actions.executeActions()
        elif not self._actions.isFastForward() and self._options.force:
            print "Push not fast-forward, forcing"
            self._actions.executeActions()
        else:
            print "Push not fast-forward:"
            self._actions.display()

    def _import_doc(self):
        return ActionDoc("import", "<src_folder>] [--force]", """
        Import organization from disk. --force option causes existing resources
        on server to be updated.""")

    def _import_file_content(self, src_file, app, name):
        self._actions.addAction(UploadContent(src_file, app, name))

    def _import_applications(self, org):
        apps_folder = self._get_application_folder()
        if not os.path.exists(apps_folder):
            return

        apps_list = os.listdir(apps_folder)
        for app_name in apps_list:
            app = Application(org.applications(), None)
            app_folder = os.path.join(apps_folder, app_name)
            app.load(app_folder)

            self._import_resource(app)

            # Push files' content
            file_list = app.get_files()
            for f in file_list:
                file_name = f.get_name()
                content_file = os.path.join(app_folder, "files", file_name)
                self._import_file_content(content_file, app, file_name)

    def _import_resource(self, local_res, force_update = False):
        res_name = local_res.get_name()
        local_uuid = local_res.get_uuid()

        # Retrieve remote resource (if it exists)
        collection = local_res.get_collection()
        remote_res = None
        try:
            remote_res = collection.get_resource(res_name)
        except ResourceNotFoundException:
            pass

        # In function of remote resource existence, queue an action
        if remote_res != None:
            remote_uuid = remote_res.get_uuid()
            if(remote_uuid == local_uuid):
                self._actions.addAction(UpdateResource(False, local_res))
            else:
                raise SyncException("There is a conflict for resource " + res_name)

#            else:
#                new_name = self._getUniqueName(res_name, collection)
#                local_res.set_name(new_name)
#                self._actions.addAction(CreateResource(False, local_res))
        elif force_update:
            self._actions.addAction(UpdateResource(True, local_res))
        else:
            self._actions.addAction(CreateResource(True, local_res))

    def _import_instance(self, host, instance):
        try:
            host.instance().get_single_resource()
            return
        except ResourceNotFoundException:
            self._actions.addAction(CreateInstance(True, host, instance))

    def _get_group_folder(self):
        return os.path.join(self._root, "groups")

    def _get_application_folder(self):
        return os.path.join(self._root, "applications")

    def _get_distribution_folder(self):
        return os.path.join(self._root, "distributions")

    def _get_platform_folder(self):
        return os.path.join(self._root, "platforms")

    def _get_environment_folder(self):
        return os.path.join(self._root, "environments")

    def _get_instance_file(self, host_folder):
        return os.path.join(host_folder, "instance.json")

    def _import_distributions(self, org):
        dists_folder = self._get_distribution_folder()
        if not os.path.exists(dists_folder):
            return

        dists_list = os.listdir(dists_folder)
        for dist_name in dists_list:
            dist = Distribution(org.distributions(), None)
            dist_folder = os.path.join(dists_folder, dist_name)
            dist.load(dist_folder)

            self._import_resource(dist)

            # Push files' content
            file_list = dist.get_files()
            for f in file_list:
                file_name = f.get_name()
                content_file = os.path.join(dist_folder, "files", file_name)
                self._import_file_content(content_file, dist, file_name)

    def _get_app_context_file(self, host_folder, name):
        return os.path.join(host_folder, "applications", name)

    def _import_organization(self):
        # Create unconnected organization
        local_org = Organization(self._api.organizations(), None)
        local_org.load(self._root)

        # Create organization
        self._import_resource(local_org)
        self._import_groups(local_org)

        self._import_applications(local_org)
        self._import_distributions(local_org)
        self._import_platforms(local_org)
        self._import_environments(local_org)

    def _import_groups(self, org):
        groups_folder = self._get_group_folder()
        if not os.path.exists(groups_folder):
            return

        groups_list = os.listdir(groups_folder)
        for group_name in groups_list:
            group = Group(org.groups(), None)
            group_folder = os.path.join(groups_folder, group_name)
            group.load(group_folder)

            # For now, groups can only be udpated
            self._import_resource(group, force_update = True)

    def _import_environments(self, org):
        envs_folder = self._get_environment_folder()
        if not os.path.exists(envs_folder):
            return

        envs_list = os.listdir(envs_folder)
        for env_name in envs_list:
            env = Environment(org.environments(), None)
            env_folder = os.path.join(envs_folder, env_name)
            env.load(env_folder)

            self._import_resource(env)

            # Push hosts
            hosts_list = os.listdir(env_folder)
            for host_name in hosts_list:
                host_dir = os.path.join(env_folder, host_name)

                # Skip files
                if os.path.isfile(host_dir):
                    continue

                host = Host(env.hosts(), None)
                host.load(host_dir)

                apps = host.get_applications()

                # Contexts are created below
                host._del_field("applications")
                host._del_field("platform")
                host._del_field("distribution")

                self._import_resource(host)

                # Import application contexts
                for app in apps:
                    context = ApplicationContext(host.applications(), None)
                    context.load_json(os.path.join(host_dir, "applications", app + ".json"))
                    self._import_resource(context)

                # Import platform context
                platform_file = os.path.join(host_dir, "platform.json")
                if os.path.exists(platform_file):
                    context = PlatformContext(host.platform(), None)
                    context.load_json(platform_file)
                    self._import_resource(context)

                # Import distribution context
                dist_file = os.path.join(host_dir, "distribution.json")
                if os.path.exists(dist_file):
                    context = DistributionContext(host.distribution(), None)
                    context.load_json(dist_file)
                    self._import_resource(context)

                # Import instance (must come at last)
                instance_file = self._get_instance_file(host_dir)
                if os.path.exists(instance_file):
                    with open(instance_file, "r") as f:
                        instance = Instance(host.instance(), json.load(f))
                        self._import_instance(host, instance)

    def _import_platforms(self, org):
        plats_folder = self._get_platform_folder()
        if not os.path.exists(plats_folder):
            return

        plats_list = os.listdir(plats_folder)
        for plat_name in plats_list:
            plat = Platform(org.platforms(), None)
            plat_folder = os.path.join(plats_folder, plat_name)
            plat.load(plat_folder)

            self._import_resource(plat)

            # Push files' content
            file_list = plat.get_files()
            for f in file_list:
                file_name = f.get_name()
                content_file = os.path.join(plat_folder, "files", file_name)
                self._import_file_content(content_file, plat, file_name)
