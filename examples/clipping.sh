#! /usr/bin/env bash

set -eu

cd "$(dirname "$BASH_SOURCE")"

for i in rainbow applejack pinkie twilight rarity fluttershy; do
    inkscape-flatten -o "clipping-$i.pdf" -c "$i" clipping.svg ponies
done
