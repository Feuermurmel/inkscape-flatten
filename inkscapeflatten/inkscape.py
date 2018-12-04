import copy
import re
import subprocess
import sys
from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory

from lxml import etree
from lxml.etree import ElementTree, Element, XMLParser

from inkscapeflatten.util import UserError
from inkscapeflatten.vendored import simplestyle, simpletransform


def _gather_layers(tree: ElementTree):
    def walk_layer(id, path, element):
        nodes = element.findall(
            '{http://www.w3.org/2000/svg}g[@{http://www.inkscape.org/namespaces/inkscape}groupmode="layer"]')

        def iter_children():
            for node in nodes:
                name = node.get('{http://www.inkscape.org/namespaces/inkscape}label')
                id = node.get('id')

                # Make sure that every layer has an ID. Otherwise we're screwed, because we won't be able to find the element again later.
                assert id is not None

                yield walk_layer(id, path + [name], node)

        return Layer(id, path, list(iter_children()))

    return walk_layer(None, [], tree)


def _get_layer_node(tree: ElementTree, layer: 'Layer'):
    if layer.id is None:
        node = tree.getroot()
    else:
        # FIXME: ID should be escaped here.
        node = tree.find('.//*[@id="{}"]'.format(layer.id))

    assert node is not None

    return node


def _get_ancestor_nodes(node: Element):
    def _iter_ancestor_nodes():
        ancestor = node

        while ancestor is not None:
            yield ancestor

            ancestor = ancestor.getparent()

    return list(_iter_ancestor_nodes())


def _set_style(node, name, value):
    style = simplestyle.parseStyle(node.get('style'))

    if value is not None:
        style[name] = value
    elif name in style:
        del style[name]

    node.set('style', simplestyle.formatStyle(style))


def _hide_deselected_layers(tree: ElementTree, layers: list):
    # We need to select at least one layer.
    assert layers

    tree = copy.deepcopy(tree)

    selected_nodes = set()
    selected_nodes_ancestors = set()

    for layer in layers:
        ancestors_nodes = _get_ancestor_nodes(_get_layer_node(tree, layer))

        selected_nodes.add(ancestors_nodes[0])
        selected_nodes_ancestors.update(ancestors_nodes)

    # Hide siblings of all nodes along the path from a selected layer to the root.
    for i in selected_nodes_ancestors - selected_nodes:
        for node in i.findall('*'):
            _set_style(node, 'display', 'none')

    # Unhide all nodes along the path from a selected layer to the root.
    for i in selected_nodes_ancestors:
        _set_style(i, 'display', None)

    return tree


def _adjust_view_box(svg_element: Element, bounds):
    # "parse" in biq air-quotes.
    def parse_measure(measure):
        value, unit = re.match(r'(.+?)(\w+)$', measure).groups()

        return float(value), unit

    width, width_unit = parse_measure(svg_element.get('width'))
    height, height_unit = parse_measure(svg_element.get('height'))
    old_xmin, old_ymin, old_xsize, old_ysize = map(float, svg_element.get('viewBox').split())

    xmin, xmax, ymin, ymax = bounds
    xsize = xmax - xmin
    ysize = ymax - ymin

    width *= xsize / old_xsize
    height *= ysize / old_ysize

    svg_element.set('width', '{}{}'.format(width, width_unit))
    svg_element.set('height', '{}{}'.format(height, height_unit))
    svg_element.set('viewBox', '{} {} {} {}'.format(xmin, ymin, xsize, ysize))


def _crop_to_layer_bounds(tree: ElementTree, layer: 'Layer'):
    tree = copy.deepcopy(tree)
    node = _get_layer_node(tree, layer)
    bounds = simpletransform.computeBBox(node, simpletransform.composeParents(node))

    _adjust_view_box(tree.getroot(), bounds)

    return tree


@contextmanager
def _safe_update_file(dest_path: Path):
    temp_path = dest_path.parent / (dest_path.name + '~')

    yield temp_path

    temp_path.rename(dest_path)


class SVGDocument:
    def __init__(self, tree: ElementTree):
        self.tree = tree
        self.layers = _gather_layers(tree)

    def save_to_pdf(self, path: Path, layers: list = None, region: 'Layer' = None):
        if layers is None:
            # Insert a dummy root layer reference to export all layers marked as visible in Inkscape.
            layers = [Layer(None, [], [])]

        tree = _hide_deselected_layers(self.tree, layers)

        if region is not None:
            tree = _crop_to_layer_bounds(tree, region)

        with _safe_update_file(path) as temp_pdf_path:
            with TemporaryDirectory() as temp_dir:
                temp_svg_path = Path(temp_dir) / 'document.svg'
                tree.write(str(temp_svg_path))

                args = [
                    'inkscape',
                    '--export-area-page',
                    '--export-pdf',
                    str(temp_pdf_path),
                    str(temp_svg_path)]

                try:
                    subprocess.run(args, check=True, stderr=subprocess.PIPE)
                except CalledProcessError as error:
                    sys.stderr.buffer.write(error.stderr)

                    # TODO: Wrap in UserError
                    raise UserError('Command failed: {}'.format(' '.join(args)))

    @classmethod
    def from_file(cls, path: Path):
        return cls(etree.parse(str(path), XMLParser(huge_tree=True)))


class Layer(Mapping):
    def __init__(self, id: str, path: list, children: list):
        self.id = id
        self.path = path

        self._items = [(i.name, i) for i in children]

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(name for name, _ in self._items)

    def __getitem__(self, item):
        for name, child in self._items:
            if name == item:
                return child
        else:
            raise KeyError(item)

    def __hash__(self):
        # It's handy than we can create sets of layers using the instance's identities.
        return id(self)

    @property
    def name(self):
        return ([''] + self.path)[-1]

    @property
    def flatten(self):
        return [self] + [j for _, child in self._items for j in child.flatten]
