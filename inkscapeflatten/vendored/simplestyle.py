"""
simplestyle.py
Two simple functions for working with inline css
and some color handling on top.

Copyright (C) 2005 Aaron Spike, aaron@ekips.org

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


def parseStyle(s):
    """Create a dictionary from the value of an inline style attribute"""
    if s is None:
      return {}
    else:
      return dict([[x.strip() for x in i.split(":")] for i in s.split(";") if len(i.strip())])


def formatStyle(a):
    """Format an inline style attribute from a dictionary"""
    return ";".join([att+":"+str(val) for att,val in a.items()])
