# Legacy scripts

Scripts can be run e.g. on `qa00.cnx.org` or on staging on `staging04.cnx.org`
or on production on `prod04.cnx.org` if you are certain what you are doing.

## Get all member list csv from legacy CNX

How to run:

```bash
./create_member-csv.sh
```

The memberlist will be written into `members.csv`.

The total numbers of legacy members can be found in `membercount.txt`.

Note: The whole process takes ~1 hour on cnx legacy production.

## Restrict member access to members only on the `accesslist.txt`

You need an `accesslist.txt` with all member ids / usernames of legacy which should still have access on the end.
This `accesslist.txt` is not provided in this repo.

Example of how an accesslist.txt looks like:

```
tom
jerry
therealmarv
```

FYI: accesslist.txt as it was run on [2020-07-02 on production link here](https://drive.google.com/file/d/1UIpFOaG2vV70SWc75amdEd96twCUoLbh/view?usp=sharing).
Details are on [issue 1014](https://github.com/openstax/cnx/issues/1014).
Please be sure that accesslist.txt is correct & up to date **before** it is run on production and **it also includes new accounts**!

To restrict access to all members except the ones on the `accesslist.txt` run this command:

```bash
./access-deny-list.sh
```

Note: The whole process takes ~1 hour on cnx legacy production.

## Debugging and checking members groups

To check/debug quickly which member groups a member belongs to you can check
a number of members with this command which checks member roles from member 0 to 100:

```bash
/var/lib/cnx/cnx-buildout/bin/instance run print-member-roles.py 0 100
```