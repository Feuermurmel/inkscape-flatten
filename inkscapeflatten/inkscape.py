import copy
import subprocess
import xml.etree.ElementTree as etree
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import ElementTree
from collections.abc import Mapping

from inkscapeflatten.vendored import simplestyle


def _gather_layers(tree: ElementTree):
    def walk_layer(element, path):
        nodes = element.findall(
            '{http://www.w3.org/2000/svg}g[@{http://www.inkscape.org/namespaces/inkscape}groupmode="layer"]')

        def iter_children():
            for node in nodes:
                name = node.get('{http://www.inkscape.org/namespaces/inkscape}label')
                id = node.get('id')

                # Make sure that every layer has an ID. Otherwise we're screwed, because we won't be able to find the element again later.
                assert id is not None

                yield walk_layer(node, path + [(name, id)])

        return Layer(path, list(iter_children()))

    return walk_layer(tree, [])


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

    def get_node_by_id(id):
        if id is None:
            node = tree.getroot()
        else:
            # FIXME: ID should be escaped here.
            node = tree.find('.//*[@id="{}"]'.format(id))

        assert node is not None

        return node

    selected_ids = set()
    selected_ancestor_ids = set()

    for layer in layers:
        # Add None to represent the root layer, which does not necessarily have an ID.
        ids = [None] + [id for _, id in layer._path_with_ids]

        selected_ids.add(ids[-1])
        selected_ancestor_ids.update(ids)

    for i in selected_ancestor_ids - selected_ids:
        for node in get_node_by_id(i).findall('*'):
            _set_style(node, 'display', 'none')

    for i in selected_ancestor_ids:
        _set_style(get_node_by_id(i), 'display', None)

    return tree


class SVGDocument:
    def __init__(self, tree: ElementTree):
        self.tree = tree
        self.layers = _gather_layers(tree)

    def save_to_pdf(self, path: Path, layers: list = None):
        if layers is None:
            # Insert a dummy root layer reference to export all layers marked as visible in Inkscape.
            layers = [Layer([], [])]

        tree = _hide_deselected_layers(self.tree, layers)
        temp_pdf_path = path.parent / (path.name + '~')

        with TemporaryDirectory() as temp_dir:
            temp_svg_path = Path(temp_dir) / 'document.svg'
            tree.write(str(temp_svg_path))

            args = [
                'inkscape',
                '--export-area-page',
                '--export-pdf',
                str(temp_pdf_path),
                str(temp_svg_path)]

            subprocess.run(args, check=True)

        temp_pdf_path.rename(path)

    @classmethod
    def from_file(cls, path: Path):
        return cls(etree.parse(str(path)))


class Layer(Mapping):
    def __init__(self, path_with_ids: list, children: list):
        # List of tuples (name, id) for all ancestors.
        self._path_with_ids = path_with_ids

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

    @property
    def path(self):
        return [name for name, _ in self._path_with_ids]

    @property
    def name(self):
        path = self.path

        if not path:
            return ''

        return path[-1]

    @property
    def flatten(self):
        return [self] + [j for _, child in self._items for j in child.flatten]
