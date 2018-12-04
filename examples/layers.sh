#! /usr/bin/env bash

set -eu

cd "$(dirname "$BASH_SOURCE")"

for i in a b c c/1 c/2; do
    inkscape-flatten -l "$i" layers.svg "layers-${i//"/"}.pdf"
done

inkscape-flatten -l a -l b layers.svg "layers-a-b.pdf"
inkscape-flatten -l a -l c/1 layers.svg "layers-a-c1.pdf"
inkscape-flatten -l c/1 -l c/2 layers.svg "layers-c1-c2.pdf"
