#!/var/lib/cnx/cnx-buildout/bin/instance run

# write member count to a file

import sys
from Products.CMFCore.utils import getToolByName
from Products.PluggableAuthService.interfaces.plugins import IRoleAssignerPlugin

site = app.objectValues("Plone Site")[0]

mtool = getToolByName(site, 'portal_membership')
mdtool = getToolByName(site, 'portal_memberdata')
member_ids = mdtool.objectIds()

filename = sys.argv[1]

print("getting total member count... (this takes a couple of minutes)")
count = len(member_ids)
print("Member count: " + str(count))

f = open(filename, "w")
f.write(str(count))
f.flush()
f.close()
