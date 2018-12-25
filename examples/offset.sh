#! /usr/bin/env bash

set -eu

cd "$(dirname "$BASH_SOURCE")"

inkscape-flatten -o "offset.pdf" offset.svg a@0,0 b@0,-15 c@0,-30 d@-30,-45 e@-60,-60