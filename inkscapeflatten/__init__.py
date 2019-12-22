import fnmatch
import re
import sys
from argparse import ArgumentParser, ArgumentTypeError
from pathlib import Path

from inkscapeflatten.inkscape import SVGDocument, Layer, Transformation
from inkscapeflatten.util import UserError


class LayerSelection:
    def __init__(self, pattern, offset):
        self.pattern = pattern
        self.offset = offset

    @classmethod
    def from_string(cls, string):

        string = string.strip()

        if len(string) == 0:
            return None

        if string.startswith('#'):
            return None

        pattern = \
            '(?P<pattern>[^@]+)' \
            '(@(?P<offset_x>[^@,]+),(?P<offset_y>[^@,]+))?$'

        match = re.match(pattern, string)

        if match is None:
            raise ArgumentTypeError('Invalid layer selection: {}'.format(string))

        selection_pattern = match.group('pattern')
        offset_x_str = match.group('offset_x')
        offset_y_str = match.group('offset_y')

        if not offset_x_str:
            offset_x = 0
        else:
            offset_x = float(offset_x_str)

        if not offset_y_str:
            offset_y = 0
        else:
            offset_y = float(offset_y_str)

        return cls(selection_pattern, (offset_x, offset_y))


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
        type=LayerSelection.from_string,
        nargs='*',
        metavar='layer_pattern',
        help='Shell-like patterns used to select which layers from the SVG file to export. Each pattern is matched agains the full path of each layer. When no patterns are given, all layers marked as "visible" are exported. Patterns can be suffixed with @<offset_x>,<offset_y> to offset the selcted layer by the specified vector.')

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

        if args.layers:
            parser.error('Only one of --layer and --list can be specified.')

        if args.clip is not None:
            parser.error('Only one of --clip and --list can be specified.')
    else:
        if args.output_pdf_path is None:
            parser.error('One of --output or --list must be specified.')
        args.layers = filter(lambda l: l is not None, args.layers)

    return args


def main(input_svg_path: Path, output_pdf_path: Path, layers: list, clip: str, list: bool):
    document = SVGDocument.from_file(input_svg_path)

    if list:
        # Do not list the root layer (which has an empty name).
        for i in document.layers.flatten[1:]:
            print('/'.join(i.path))
    else:
        transformation_by_layer = {}

        if layers:
            selected_layers = set()

            for i in layers:
                for j in _select_layers(document, i.pattern):
                    selected_layers.add(j)

                    if i.offset != (0, 0):
                        # FIXME: Offset for same layer may be specified through multiple selections.
                        transformation_by_layer[j] = Transformation.from_offset(i.offset)
        else:
            selected_layers = None

        document = document.with_transformed_layers(transformation_by_layer)

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
