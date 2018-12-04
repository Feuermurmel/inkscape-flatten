"""
inkex.py
A helper module for creating Inkscape extensions

Copyright (C) 2005,2010 Aaron Spike <aaron@ekips.org> and contributors

Contributors:
  Aurélio A. Heckert <aurium(a)gmail.com>
  Bulia Byak <buliabyak@users.sf.net>
  Nicolas Dufour, nicoduf@yahoo.fr
  Peter J. R. Moulder <pjrm@users.sourceforge.net>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""


# a dictionary of all of the xmlns prefixes in a standard inkscape doc
NSS = {
'sodipodi' :'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
'cc'       :'http://creativecommons.org/ns#',
'ccOLD'    :'http://web.resource.org/cc/',
'svg'      :'http://www.w3.org/2000/svg',
'dc'       :'http://purl.org/dc/elements/1.1/',
'rdf'      :'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
'inkscape' :'http://www.inkscape.org/namespaces/inkscape',
'xlink'    :'http://www.w3.org/1999/xlink',
'xml'      :'http://www.w3.org/XML/1998/namespace'
}


def addNS(tag, ns=None):
    val = tag
    if ns is not None and len(ns) > 0 and ns in NSS and len(tag) > 0 and tag[0] != '{':
        val = "{%s}%s" % (NSS[ns], tag)
    return val
