
"""rsf2model - extracts presence implications from kconfig dumps"""

# Copyright (C) 2011 Christian Dietrich <christian.dietrich@informatik.uni-erlangen.de>
# Copyright (C) 2012 Manuel Zerpies <manuel.f.zerpies@ww.stud.uni-erlangen.de>
# Copyright (C) 2014-2015 Stefan Hengelein <stefan.hengelein@fau.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from vamos.rsf2model import tools
from vamos.rsf2model.BoolParser import BoolParser
from vamos.rsf2model.helper import tree_change, BoolRewriterException


class BoolRewriter(tools.UnicodeMixin):
    ELEMENT = "in"

    def __init__(self, rsf, expr, eval_to_module = True):
        tools.UnicodeMixin.__init__(self)
        self.expr = BoolParser(expr).to_bool()
        if type(self.expr) == str or self.expr[0] == BoolParser.NOT:
            self.expr = [BoolParser.AND, self.expr]
        self.rsf = rsf
        self.eval_to_module = eval_to_module

    def rewrite_not(self):
        self.expr = tree_change(self.__rewrite_not, self.expr)
        return self.expr

    def __rewrite_not(self, tree):
        if tree[0] == BoolParser.NOT and type(tree[1]) == list:
            tree = tree[1]
            if tree[0] == BoolParser.AND:
                tree = [BoolParser.OR] + [[BoolParser.NOT, x] for x in tree[1:]]
                return tree_change(self.__rewrite_not, tree)
            elif tree[0] == BoolParser.OR:
                tree = [BoolParser.AND] + [[BoolParser.NOT, x] for x in tree[1:]]
                return tree_change(self.__rewrite_not, tree)
            elif tree[0] == BoolParser.NOT:
                return tree_change(self.__rewrite_not, tree[1])
            elif tree[0] == BoolParser.EQUAL:
                tree[0] = BoolParser.NEQUAL
                return tree
            elif tree[0] == BoolParser.NEQUAL:
                tree[0] = BoolParser.EQUAL
                return tree

    def rewrite_tristate(self):
        self.expr = tree_change(self.__rewrite_tristate, self.expr)
        return self.expr

    def __rewrite_tristate(self, tree):
        #pylint: disable=R0912

# Dependencies reduce the upper limit of a symbol (tristate means 3 values: y=2, m=1, n=0).
# When the dependency of a symbol evaluates to m (=1), the symbol cannot
# evaluate to y (=2) anymore. Example:
#
# config A | tristate | depends on B
# config B | tristate
#
# B=y  -> A=m || A=n || A=y
# B=m  -> A=m || A=n
# B=n  -> /
#
# config A | tristate | depends on !B
# config B | tristate
#
# B=y  -> /
# B=m  -> A=m || A=n
# B=n  -> A=m || A=n || A=y

        def tristate_not(symbol):
            if symbol in self.rsf.options() and self.rsf.options()[symbol].tristate():
                if self.eval_to_module:
                    # when B is a tristate and is allowed to be 'm', !B means (B!=y || B=m).
                    return [BoolParser.OR,
                            [BoolParser.NEQUAL, symbol, "y"],
                            [BoolParser.EQUAL, symbol, "m"]]
                else:
                    return [BoolParser.EQUAL,  symbol, "n"]
            return [BoolParser.NOT, symbol]

        def tristate(symbol):
            if symbol in self.rsf.options() and self.rsf.options()[symbol].tristate():
                if self.eval_to_module:
                    return [BoolParser.NEQUAL, symbol, "n"]
                else:
                    return [BoolParser.EQUAL,  symbol, "y"]
            return symbol

        if tree[0] in [BoolParser.AND, BoolParser.OR]:
            for i in range(1, len(tree)):
                if type(tree[i]) == list:
                    if tree[i][0] == BoolParser.NOT:
                        tree[i] = tristate_not(tree[i][1])
                    else:
                        tree[i] = tree_change(self.__rewrite_tristate, tree[i])
                else:
                    tree[i] = tristate(tree[i])
            return tree

    def rewrite_choice(self):
        """Removes all CHOICE_ items"""
        def __recr(tree):
            tree = [x for x in tree if not(type(x) == str and x.startswith("CHOICE_"))]
            if len(tree) == 1:
                return []
            return tree

        self.expr = tree_change(__recr, self.expr)
        return self.expr

    def rewrite_symbol(self):
        self.expr = tree_change(self.__rewrite_symbol, self.expr)
        return self.expr

    def __rewrite_symbol(self, tree):
        def to_symbol(tree):
            if type(tree) in [list, tuple]:
                return tree_change(self.__rewrite_symbol, tree)
            if tree == "m":
                if self.eval_to_module:
                    # m is true, if the expression can evaluate to module
                    self.rsf.has_ignored_symbol = True
                    return tools.new_free_item()
                else:
                    # otherwise it is false, because expr = y is needed
                    a = tools.new_free_item()
                    return [BoolParser.AND, a, [BoolParser.NOT, a]]
            elif tree == "unknown":
                return tools.new_free_item()
            return self.rsf.symbol(tree)

        if tree[0] in [BoolParser.NOT, BoolParser.AND, BoolParser.OR]:
            return [tree[0]] + map(to_symbol, tree[1:])
        elif tree[0] == BoolParser.EQUAL:
            return self.__rewrite_symbol_equal(tree)
        elif tree[0] == BoolParser.NEQUAL:
            return self.__rewrite_symbol_nequal(tree)

    def __rewrite_symbol_equal(self,tree):
        left = tree[1]
        right = tree[2]
        left_y = self.rsf.symbol(left)
        left_m = self.rsf.symbol_module(left)
        right_y = self.rsf.symbol(right)
        right_m = self.rsf.symbol_module(right)

        left_value = left.startswith("CVALUE_")
        right_value = right.startswith("CVALUE_")

        if left.lower() in ["y", "n", "m"]:
            right, left = left, right
        if left.lower() in ["y", "n", "m"]:
            raise BoolRewriterException("compare literal with literal")

        # if anything is compared with a non-existent symbol, it can never be true
        if not left_value and not left in self.rsf.options():
            self.rsf.has_compare_with_nonexistent = True
            return [BoolParser.AND, left_y, "CONFIG_COMPARE_WITH_NONEXISTENT"]
        elif not right.lower() in ["y", "n", "m"] and not right_value \
                                                  and not right in self.rsf.options():
            self.rsf.has_compare_with_nonexistent = True
            return [BoolParser.AND, right_y, "CONFIG_COMPARE_WITH_NONEXISTENT"]

        if right == "y":
            return left_y
        elif right == "m":
            return left_m
        elif right == "n":
            return [BoolParser.AND,
                    [BoolParser.NOT, left_m],
                    [BoolParser.NOT, left_y]]

        # Symbol == Symbol
        result = [BoolParser.OR,
                  [BoolParser.AND, left_y, right_y], # Either both y
                  [BoolParser.AND, # Or everything disabled
                   [BoolParser.NOT, left_y], [BoolParser.NOT, right_y]]]

        # if both items are tristate, add comparisons between tristate symbols
        if left in self.rsf.options() and right in self.rsf.options() \
                and self.rsf.options()[left].tristate() and self.rsf.options()[right].tristate():
            result[-1].append([BoolParser.NOT, left_m])
            result[-1].append([BoolParser.NOT, right_m])
            result.append([BoolParser.AND, left_m, right_m]) # both m

        return result

    def __rewrite_symbol_nequal(self,tree):
        left = tree[1]
        right = tree[2]
        left_y = self.rsf.symbol(left)
        left_m = self.rsf.symbol_module(left)
        right_y = self.rsf.symbol(right)
        right_m = self.rsf.symbol_module(right)

        left_value = left.startswith("CVALUE_")
        right_value = right.startswith("CVALUE_")

        if left.lower() in ["y", "n", "m"]:
            right, left = left, right
        if left.lower() in ["y", "n", "m"]:
            raise BoolRewriterException("compare literal with literal")

        # if anything is compared with a non-existent symbol, it is always true
        if (not left_value and not left in self.rsf.options()) or \
           (not right.lower() in ["y", "n", "m"] and not right_value \
                                                 and not right in self.rsf.options()):
            return tools.new_free_item()

        if right == "y":
            return [BoolParser.NOT, left_y]
        elif right == "m":
            return [BoolParser.NOT, left_m]
        elif right == "n":
            return [BoolParser.OR, left_m, left_y]

        # Symbol != Symbol
        result = [BoolParser.OR,
                  [BoolParser.AND, left_y, [BoolParser.NOT, right_y]],
                  [BoolParser.AND, [BoolParser.NOT, left_y], right_y]]

        # if both items are tristate, add comparisons between tristate symbols
        if left in self.rsf.options() and right in self.rsf.options() \
                and self.rsf.options()[left].tristate() and self.rsf.options()[right].tristate():
            result.append([BoolParser.AND, left_m, [BoolParser.NOT, right_m]])
            result.append([BoolParser.AND, [BoolParser.NOT, left_m], right_m])

        return result


    def dump(self):
        def __concat(tree):
            if not type(tree) in [list, tuple]:
                return tree
            if tree[0] == BoolParser.NOT:
                return "!" + tree[1]
            elements = []
            for e in tree[1:]:
                elements.append(__concat(e))
            cat = " && "
            if tree[0] == BoolParser.OR:
                cat = " || "
            if len(elements) == 1:
                return cat.join(elements)
            return "(" + cat.join(elements) + ")"
        if self.expr == []:
            return ""
        return __concat(self.expr)

    def rewrite(self):
        self.rewrite_not()
        self.rewrite_choice()
        self.rewrite_tristate()
        self.rewrite_symbol()
        return self

    def __unicode__(self):
        return self.dump()
