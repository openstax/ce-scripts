#!/bin/bash
set -euo pipefail
countfile=membercount.txt
accesslist=accesslist.txt

function deny_access() {
    echo Checking access for members from $1 to $2
    /var/lib/cnx/cnx-buildout/bin/instance run check-member-deny.py $accesslist $1 $2
}

function backup_file() {
    if [ -f "$1" ]; then
        mv -f "$1" "$1.bak"
    fi
}

# delete/backup old files
backup_file $countfile

# get member count
echo get member count
/var/lib/cnx/cnx-buildout/bin/instance run getmembercount.py $countfile

if [ -f "$countfile" ]; then
    membercount=$(head -n 1 $countfile)
else
    echo "$countfile missing (total number of legacy members)"
    exit 1
fi
stepcount=10000
steps=$((membercount / stepcount))
remainder=$((membercount % stepcount))

if [ $steps -gt 0 ]; then # never do negative stepping
    for step in $(seq 0 $((steps - 1))); do
        start=$((step * stepcount))
        end=$((start + stepcount - 1))
        get_members $start $end
    done
fi
if [ $remainder -gt 0 ]; then
    start=$((steps * stepcount))
    end=$((start + remainder - 1))
    get_members $start $end
fi

echo Finished.
