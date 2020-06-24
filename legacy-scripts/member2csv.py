# write all members to ~/members.csv file

import sys
import csv
from Products.CMFCore.utils import getToolByName
from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin


def get_member_data(start, end):

    def get_member_info(member_id):
        site = app.objectValues("Plone Site")[0]
        mtool = getToolByName(site, 'portal_membership')
        return mtool.getMemberById(member_id)

    def get_member_ids():
        site = app.objectValues("Plone Site")[0]
        mdtool = getToolByName(site, 'portal_memberdata')
        return mdtool.objectIds()

    member_ids = get_member_ids()
    for index in range(start, end+1):
        member = get_member_info(member_ids[index])
        if member:
            member_id_name = member.id
            member_email = member.email
            member_firstname = member.firstname
            member_lastname = member.surname
            member_fullname = member.fullname
            member_roles = member.getRoles()
            formatted_member_roles = " ".join(member_roles)
            yield [member_id_name, member_email, member_firstname, member_lastname, member_fullname, formatted_member_roles]


def main():
    csv_filename = sys.argv[1]
    start_index = int(sys.argv[2])
    end_index = int(sys.argv[3])

    if start_index > 0:
        writemode = 'a'
    else:
        writemode = 'w'

    csv_file = open(csv_filename, mode=writemode)
    writer = csv.writer(csv_file, delimiter=',',
                        quotechar='"', quoting=csv.QUOTE_MINIMAL)
    if start_index == 0:
        # write header in old python 2.4 way
        writer.writerow(['id', 'email', 'first_name',
                         'last_name', 'full_name', 'roles'])

    for member in get_member_data(start_index, end_index):
        writer.writerow(member)

    csv_file.flush()
    csv_file.close()


if __name__ == "__main__":
    main()
