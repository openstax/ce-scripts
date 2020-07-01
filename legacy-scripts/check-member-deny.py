# check if member is in access list and deny access by removing member from all groups if not

import sys
import csv
from time import sleep
from Products.CMFCore.utils import getToolByName
from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin


def deny_member_roles(access_list, start, end):

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
            # TODO: write this errors which should not occur maybe into a file?
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
            # member_roles = member.getRoles()
            # formatted_member_roles = " ".join(member_roles)
            if member_id_name in access_list:
                # do nothing
                print('%s in access list' % member_id_name)
            else:
                # DENY member
                # which means: remove all groups from member so that login won't work anymore
                member_roles = get_member_roles(acl_users, portal_role_manager, member_id_name)
                if member_roles:
                    for role in member_roles:
                        portal_role_manager.removeRoleFromPrincipal(role, member_id_name)
    import transaction; transaction.commit()

def main():
    access_list_filename = sys.argv[1]
    start_index = int(sys.argv[2])
    end_index = int(sys.argv[3])

    # csv_file = open(csv_filename, mode=writemode)

    # note: whitelist contains ONLY member ids aka usernames
    access_list_file = open(access_list_filename, mode='r')
    access_list = access_list_file.read().splitlines()
    access_list_file.close()

    deny_member_roles(access_list, start_index, end_index)

if __name__ == "__main__":
    main()
