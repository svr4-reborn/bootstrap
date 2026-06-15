#!/usr/bin/env bash

gdb -ex "target remote localhost:1234" \
 ../svr4-bootstrap-build/packages/uts/etc/conf/cf.d/unix