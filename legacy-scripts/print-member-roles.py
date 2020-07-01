import sys
import csv
from time import sleep
from Products.CMFCore.utils import getToolByName
from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin


def print_member_roles(start, end):

    def get_member_info(member_id):
        site = app.objectValues("Plone Site")[0]
        mtool = getToolByName(site, 'portal_membership')
        return mtool.getMemberById(member_id)

    def get_member_ids():
        site = app.objectValues("Plone Site")[0]
        mdtool = getToolByName(site, 'portal_memberdata')
        return mdtool.objectIds()

    def get_member_roles(acl_users, portal_role_manager, member_id):
        user = acl_users.getUserById(member_id)
        try:
            roles = portal_role_manager.getRolesForPrincipal(user)
        except:
            print('=== ERROR getting roles for %s ===' % member_id)
            roles = tuple()
        return roles

    member_ids = get_member_ids()

    # intialize roles variables
    site = app.objectValues("Plone Site")[0]
    acl_users = getToolByName(site, 'acl_users')
    portal_role_manager = acl_users.portal_role_manager

    for index in range(start, end+1):
        sleep(0.01)     # sleep 10ms to reduce load on production legacy
        member = get_member_info(member_ids[index])
        if member:
            member_id_name = member.id
            member_roles = get_member_roles(acl_users, portal_role_manager, member_id_name)
            print("User: %s" % member_id_name)
            print("Roles: %s" % member_roles)

def main():
    start_index = int(sys.argv[2])
    end_index = int(sys.argv[3])

    print_member_roles(start_index, end_index)

if __name__ == "__main__":
    main()
