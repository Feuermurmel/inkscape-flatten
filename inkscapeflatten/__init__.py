import itertools
from argparse import ArgumentParser
from pathlib import Path

from inkscapeflatten.inkscape import SVGDocument


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('input_svg_path', type=Path)
    parser.add_argument('output_pdf_path', type=Path)

    return parser.parse_args()


def main(input_svg_path: Path, output_pdf_path: Path):
    document = SVGDocument.from_file(input_svg_path)

    document.save_to_pdf(output_pdf_path)


def script_main():
    main(**vars(parse_args()))
