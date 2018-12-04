#! /usr/bin/env bash

set -eu

cd "$(dirname "$BASH_SOURCE")"

for i in rainbow applejack pinkie twilight rarity fluttershy; do
    inkscape-flatten -l ponies -c "$i" clipping.svg "clipping-$i.pdf"
done
