#! /usr/bin/env bash

set -eu

cd "$(dirname "$BASH_SOURCE")"

for i in a b c c/1 c/2; do
    inkscape-flatten -o "layers-${i//"/"}.pdf" layers.svg "$i"
done

inkscape-flatten -o "layers-a-b.pdf" layers.svg a b
inkscape-flatten -o "layers-a-c1.pdf" layers.svg a c/1
inkscape-flatten -o "layers-c1-c2.pdf" layers.svg c/1 c/2
