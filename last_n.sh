#!/bin/bash

temp_file=$(mktemp)

tail -$1 $2 > $temp_file

head -8 $2 | cat - $temp_file > runAventa_${1}.out

rm $temp_file
