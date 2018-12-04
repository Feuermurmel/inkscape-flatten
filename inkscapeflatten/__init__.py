import fnmatch
import sys
from argparse import ArgumentParser
from pathlib import Path

from inkscapeflatten.inkscape import SVGDocument, Layer
from inkscapeflatten.util import UserError


def _select_layers(document: SVGDocument, pattern: str):
    layers = [document.layers]

    for pattern_part in pattern.split('/'):
        layers = [
            child
            for i in layers
            for name, child in i.items()
            if fnmatch.fnmatchcase(name, pattern_part)]

    if not layers:
        raise UserError('Pattern did not match any layers: {}'.format(pattern))

    return layers


def _get_layer(document: SVGDocument, path: str):
    layer = document.layers

    for i in path.split('/'):
        layer = layer.get(i)

        if layer is None:
            raise UserError('Layer not found: {}'.format(path))

    return layer


def parse_args():
    parser = ArgumentParser()

    parser.add_argument(
        'input_svg_path',
        type=Path,
        help='Path from which to load an Inkscape SVG file.')

    parser.add_argument(
        '-o',
        '--output',
        type=Path,
        metavar='output_pdf_path',
        dest='output_pdf_path',
        help='Path to which a PDF contining the selected layers should be written to.')

    parser.add_argument(
        'layers',
        nargs='*',
        metavar='layer_pattern',
        help='Shell-like patterns used to select which layers from the SVG file to export. Each pattern is matched agains the full path of each layer. When no patterns are given, all layers marked as "visible" are exported.')

    parser.add_argument(
        '-c',
        '--clip',
        metavar='clip_layer',
        help='Full path of a layer used to clip the generated PDF file. The document is clipped to the bounding box of the this layer\'s content before exporting.')

    parser.add_argument(
        '-L',
        '--list',
        action='store_true',
        help='Instead of exporting the SVG document to a PDF, print a list of the full paths of all layers.')

    args = parser.parse_args()

    if args.list:
        if args.output_pdf_path is not None:
            parser.error('Only one of output_pdf_path and --list can be specified.')

        if args.layers is not None:
            parser.error('Only one of --layer and --list can be specified.')

        if args.clip is not None:
            parser.error('Only one of --clip and --list can be specified.')
    else:
        if args.output_pdf_path is None:
            parser.error('One of output_pdf_path or --list must be specified.')

    return args


def main(input_svg_path: Path, output_pdf_path: Path, layers: list, clip: str, list: bool):
    document = SVGDocument.from_file(input_svg_path)

    if list:
        # Do not list the root layer (which has an empty name).
        for i in document.layers.flatten[1:]:
            print('/'.join(i.path))
    else:
        if layers is None:
            selected_layers = None
        else:
            selected_layers = set(j for i in layers for j in _select_layers(document, i))

        if clip is None:
            clip_layer = None
        else:
            clip_layer = _get_layer(document, clip)

        document.save_to_pdf(output_pdf_path, selected_layers, clip_layer)


def script_main():
    try:
        main(**vars(parse_args()))
    except UserError as e:
        print('Error: {}'.format(e), file=sys.stderr)
