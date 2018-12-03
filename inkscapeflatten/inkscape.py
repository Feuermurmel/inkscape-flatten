import copy
import subprocess

from lxml import etree
from lxml.etree import ElementTree
from pathlib import Path
from tempfile import TemporaryDirectory
from collections.abc import Mapping

from inkscapeflatten.vendored import simplestyle


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


def _get_ancestor_nodes(node):
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

    def get_ancestor_nodes(layer):
        if layer.id is None:
            node = tree.getroot()
        else:
            # FIXME: ID should be escaped here.
            node = tree.find('.//*[@id="{}"]'.format(layer.id))

        assert node is not None

        return _get_ancestor_nodes(node)

    selected_nodes = set()
    selected_nodes_ancestors = set()

    for layer in layers:
        nodes = get_ancestor_nodes(layer)

        selected_nodes.add(nodes[0])
        selected_nodes_ancestors.update(nodes)

    # Hide siblings of all nodes along the path from a selected layer to the root.
    for i in selected_nodes_ancestors - selected_nodes:
        for node in i.findall('*'):
            _set_style(node, 'display', 'none')

    # Unhide all nodes along the path from a selected layer to the root.
    for i in selected_nodes_ancestors:
        _set_style(i, 'display', None)

    return tree


class SVGDocument:
    def __init__(self, tree: ElementTree):
        self.tree = tree
        self.layers = _gather_layers(tree)

    def save_to_pdf(self, path: Path, layers: list = None):
        if layers is None:
            # Insert a dummy root layer reference to export all layers marked as visible in Inkscape.
            layers = [Layer(None, [], [])]

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
