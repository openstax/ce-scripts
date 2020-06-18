#!/bin/bash
function get_members() {
    echo start $1 end $2
}
membercount=20001
stepcount=10000
steps=$((membercount / stepcount))
remainder=$((membercount % stepcount))

echo $steps
echo $remainder
for step in $(seq 0 $((steps - 1))); do
    start=$((step * stepcount))
    end=$((start + stepcount - 1))
    get_members $start $end
done
if [ $remainder -gt 0 ]; then
    start=$((steps * stepcount))
    end=$((start + remainder - 1))
    get_members $start $end
fi
