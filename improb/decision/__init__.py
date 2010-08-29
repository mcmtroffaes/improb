# improb is a Python module for working with imprecise probabilities
# Copyright (c) 2008-2010, Matthias Troffaes
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""A module with utility functions for decision making."""

from __future__ import division, absolute_import, print_function

def _print_rst_table(rows, file=None):
    """Helper function to print a table in reStructured Text format."""
    maxwidth = [max((len(row[i]) if row[i] else 0)
                    for row in rows)
                for i in xrange(len(rows[0]))]
    print("+" + "+".join("{0:-<{1}}".format('', width + 2)
                         for width in maxwidth)
          + "+", file=file)
    for j, row in enumerate(rows):
        print("|", end="", file=file)
        for i in xrange(len(row)):
            elem = row[i]
            width = maxwidth[i]
            if elem is not None:
                print(" {0:^{1}} ".format(elem, width), end="", file=file)
                print("|", end="", file=file)
            else:
                print(" {0:^{1}} ".format("", width), end="", file=file)
                if i == len(row) - 1 or row[i+1] is not None:
                    print("|", end="", file=file)
                else:
                    print(" ", end="", file=file)
        print("", file=file)
        print("+", end="", file=file)
        for i in xrange(len(row)):
            elem = row[i]
            width = maxwidth[i]
            if elem is not None:
                print("{0:-<{1}}".format("", width + 2), end="", file=file)
                print("+", end="", file=file)
            else:
                if j + 1 == len(rows) or rows[j+1][i] is not None:
                    print("{0:-<{1}}".format("", width + 2), end="", file=file)
                    print("+", end="", file=file)
                else:
                    print("{0: <{1}}".format("", width + 2), end="", file=file)
                    if i == len(row) - 1 or row[i+1] is not None:
                        print("+", end="", file=file)
                    else:
                        print(" ", end="", file=file)
        print("", file=file)

def _get_sign(val):
    """Helper function to get the sign of a value."""
    if val > 1e-6:
        return '**+**'
    elif val < -1e-6:
        return '**-**'
    else:
        return '**0**'

def print_rst_solution(
    pspace, decisions, gambles, credalset,
    float_format="{0: g}", file=None):
    """Print tables with detailed calculations for solving a static
    decision problem.

    >>> pspace = ["A", "B", "C"]
    >>> decisions = ["left", "right"]
    >>> gambles = [[-10, -5, 10], [1, 1, 1]]
    >>> credalset = [[0.1, 0.45, 0.45], [0.4, 0.3, 0.3], [0.3, 0.2, 0.5]]
    >>> print_rst_solution(pspace, decisions, gambles, credalset)
    +-------------------+-----+-----+-----+-------+-------+-------+-------+-------+
    |                   | *A* | *B* | *C* | *p0*  | *p1*  | *p2*  | *lpr* | *upr* |
    +-------------------+-----+-----+-----+-------+-------+-------+-------+-------+
    |        *A*        |                 |  0.1  |  0.4  |  0.3  |               |
    +-------------------+                 +-------+-------+-------+               +
    |        *B*        |                 |  0.45 |  0.3  |  0.2  |               |
    +-------------------+                 +-------+-------+-------+               +
    |        *C*        |                 |  0.45 |  0.3  |  0.5  |               |
    +-------------------+-----+-----+-----+-------+-------+-------+-------+-------+
    |      *left*       | -10 | -5  |  10 |  1.25 | -2.5  |   1   | -2.5  |  1.25 |
    +-------------------+-----+-----+-----+-------+-------+-------+-------+-------+
    |      *right*      |  1  |  1  |  1  |   1   |   1   |   1   |   1   |   1   |
    +-------------------+-----+-----+-----+-------+-------+-------+-------+-------+
    | *right* \- *left* |                 | **-** | **+** | **0** | **-** |       |
    +-------------------+                 +-------+-------+-------+-------+       +
    | *left* \- *right* |                 | **+** | **-** | **0** | **-** |       |
    +-------------------+-----+-----+-----+-------+-------+-------+-------+-------+
    <BLANKLINE>
    +------------+--------+---------+
    |            | *left* | *right* |
    +------------+--------+---------+
    | \- *left*  | **0**  |  **-**  |
    +------------+--------+---------+
    | \- *right* | **-**  |  **0**  |
    +------------+--------+---------+
    """
    rows = []
    rows.append([None]
                + ['*{0}*'.format(w) for w in pspace]
                + ['*p{0}*'.format(i) for i, p in enumerate(credalset)]
                + ['*lpr*', '*upr*'])
    for j, w in enumerate(pspace):
        rows.append(['*{0}*'.format(w)]
                    + [None for _ in pspace]
                    + [float_format.format(p[j]) for p in credalset]
                    + [None, None])
    for gamble, dec in zip(gambles, decisions):
        rows.append(['*{0}*'.format(dec)]
                    + [float_format.format(gamble[j])
                       for j in xrange(len(pspace))]
                    + [float_format.format(
                           sum(gamble[j] * p[j]
                               for j in xrange(len(pspace))))
                       for p in credalset]
                    + [float_format.format(
                           min(sum(gamble[j] * p[j]
                                   for j in xrange(len(pspace)))
                               for p in credalset))]
                    + [float_format.format(
                           max(sum(gamble[j] * p[j]
                                   for j in xrange(len(pspace)))
                               for p in credalset))]
                    )
    for ref_gamble, ref_dec in zip(gambles, decisions):
        for other_gamble, other_dec in zip(gambles, decisions):
            if ref_gamble is other_gamble:
                continue
            gamble = [ox - x for ox, x in zip(other_gamble, ref_gamble)]
            rows.append(
                    ["*{0}* \\- *{1}*".format(other_dec, ref_dec)]
                    + [None #float_fmt.format(gamble[j])
                       for j in xrange(len(pspace))]
                    + [#float_fmt.format(
                       _get_sign(
                           sum(gamble[j] * p[j]
                               for j in xrange(len(pspace))))
                      for p in credalset]
                    + [#float_fmt.format(
                       _get_sign(
                           min(sum(gamble[j] * p[j]
                                   for j in xrange(len(pspace)))
                               for p in credalset))]
                    + [None]
                    )
    _print_rst_table(rows, file=file)
    # decision matrix
    rows = []
    rows.append(
        [None]
        + ["*{0}*".format(dec) for dec in decisions])
    for ref_gamble, ref_dec in zip(gambles, decisions):
        rows.append(["\\- *{0}*".format(ref_dec)])
        for other_gamble, other_dec in zip(gambles, decisions):
            gamble = [ox - x for ox, x in zip(other_gamble, ref_gamble)]
            lpr = min(sum(gamble[j] * p[j]
                          for j in xrange(len(pspace)))
                      for p in credalset)
            rows[-1].append(_get_sign(lpr))
    print('', file=file)
    _print_rst_table(rows, file=file)
