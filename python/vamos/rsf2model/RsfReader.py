
"""rsf2model - extracts presence implications from kconfig dumps"""

# Copyright (C) 2011 Christian Dietrich <christian.dietrich@informatik.uni-erlangen.de>
# Copyright (C) 2014 Andreas Ruprecht <rupran@einserver.de>
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

from vamos.rsf2model.BoolRewriter import BoolRewriter
from vamos.rsf2model.helper import BoolParserException
from vamos.rsf2model import tools

import shlex


class RsfReader:
    def __init__(self, fd):
        """Read rsf file and store all relations within in database"""
        keys = ["Item", "HasPrompts", "Default", "ItemSelects", "Depends",
                "Choice", "ChoiceItem", "Definition"]

        self.database = {}
        for key in keys:
            self.database[key] = []

        for line in fd.readlines():
            # ignore comment lines in Rsf-Files
            if line.startswith("#"):
                continue
            try:
                row = shlex.split(line)
            except ValueError:
                print "Couldn't parse %s" % line
                continue
            if len(row) > 1 and row[0] in keys:
                self.database[row[0]].append(row[1:])

        self.has_ignored_symbol = False
        self.has_compare_with_nonexistent = False

    @staticmethod
    def symbol(name):
        if " " in name:
            raise OptionInvalid()

        return "CONFIG_%s" % name

    @staticmethod
    def symbol_module(name):
        if " " in name:
            raise OptionInvalid()

        return "CONFIG_%s_MODULE" % name

    @tools.memoized
    def options(self):
        """Returns all configuration options"""

        # Collect all options
        tristate = {}
        omnipresent = {}
        options = set()
        for item in self.database["Item"]:
            if not item[1].lower() in ["boolean", "bool", "tristate", "integer", "string", "hex"]:
                continue
            if len(item) < 2:
                continue
            options.add(item[0])
            tristate[item[0]] = item[1].lower() == "tristate"
            omnipresent[item[0]] = False

        # Map them to options
        result = {}
        for option_name in options:
            result[option_name] = Option(self, option_name, tristate[option_name], omnipresent[option_name])

        for item in self.database["Choice"]:
            if len(item) < 2: continue
            tristate = item[2] == "tristate"
            required = item[1] == "required"
            result[item[0]] = Choice(self, item[0], tristate = tristate, required = required)
            if tristate:
                result[item[0] + "_META"] = ChoiceMeta(result[item[0]])

        return result

    @tools.memoized
    def collect(self, key, col = 0, multival = False):
        """Collect all database keys and put them by the n'th column in a dict"""

        result = {}
        for item in self.database[key]:
            if len(item) < col: continue
            if multival:
                if item[col] in result:
                    result[item[col]].append(item[0:col] + item[col+1:])
                else:
                    result[item[col]] = [item[0:col] + item[col+1:]]
            else:
                result[item[col]] = item[0:col] + item[col+1:]
        return result

    @tools.memoized
    def depends(self):
        deps = self.collect("Depends", 0, True)
        for k, v in deps.items():
            v = [x[0] for x in v]
            if len(v) > 1:
                deps[k] = ["(" + ") || (".join(v) + ")"]
            else:
                deps[k] = v
        return deps

    @tools.memoized
    def get_defined_symbols(self):
        """ Return all defined symbols as a list.  Note that the list may
        include duplicates. """
        symbols = self.database.get('Item')
        symbols.extend(self.database.get('ChoiceItem'))
        return [x[0] for x in symbols]

    def is_defined(self, symbol):
        """Returns True if @symbol is defined, otherwise False is returned."""
        return symbol in self.get_defined_symbols()

    def is_bool_tristate(self, symbol):
        """Returns True if symbol is boolean or tristate, otherwise False is
        returned."""
        return self.get_type(symbol) in ["boolean", "bool", "tristate"]

    def get_type(self, symbol):
        """Get data type of symbol. Returns 'None' if item is not found."""
        return self.collect("Item", 0, True).get(symbol, [[None]])[0][0]

    def get_depends(self, symbol):
        """Get dependencies of symbol. Returns 'None' if item is not found."""
        return self.collect("Depends").get(symbol, [None])[0]

    def get_selects(self, symbol):
        """Get selects of symbol. Returns [] if item is not found."""
        return self.collect("ItemSelects", 0, True).get(symbol, [])

    def get_prompts(self, symbol):
        """Get prompts of symbol. Returns 'None' if item is not found."""
        return self.collect("HasPrompts").get(symbol, [None])[0]

    def get_defaults(self, symbol):
        """Get default of symbol. Returns [] if item is not found."""
        return self.collect("Default", 0, True).get(symbol, [])

    def get_definition(self, symbol):
        """Get definition of symbol. Returns 'None' if item is not found."""
        return self.collect("Definition").get(symbol, [None])[0]


class ItemRsfReader(dict):

    def __init__(self, fd):
        """ Read rsf file and store item types in a dict."""
        super(ItemRsfReader, self).__init__()

        for line in fd:
            if not line.startswith("Item\t"):
                continue
            tokens = line.split()
            self[tokens[1]] = tokens[2]

    def is_bool_tristate(self, symbol):
        """Returns true if symbol is boolean or tristate, otherwise false is returned."""

        return self.get_type(symbol) in ["boolean", "bool", "tristate"]

    def get_type(self, symbol):
        """ Get data type of symbol or None if item is not found."""
        if symbol.startswith("CONFIG_"):
            symbol = symbol[7:]
        if symbol in self:
            return self[symbol]
        return None

class OptionInvalid(Exception):
    pass

class OptionNotTristate(Exception):
    pass

class Option (tools.Repr):
    def __init__(self, rsf, name, tristate = False, omnipresent = False):
        tools.Repr.__init__(self)
        self.rsf = rsf
        self.name = name
        self._tristate = tristate
        self._omnipresent = omnipresent

    def omnipresent(self):
        return self._omnipresent

    def set_omnipresent(self, value):
        self._omnipresent = value

    def tristate(self):
        return self._tristate

    def symbol(self):
        if " " in self.name:
            raise OptionInvalid()

        return "CONFIG_%s" % self.name

    def symbol_module(self):
        if " " in self.name:
            raise OptionInvalid()

        if not self._tristate:
            raise OptionNotTristate()
        return "CONFIG_%s_MODULE" % self.name

    def prompts(self):
        prompts = self.rsf.collect("HasPrompts")
        return int(prompts.get(self.name, ["-1"])[0])

    def get_type(self):
        return self.rsf.get_type(self.name)

    def hex(self):
        return self.get_type() == 'hex'

    def string(self):
        return self.get_type() == 'string'

    def dependency(self, eval_to_module = True):
        depends = self.rsf.depends()
        if not self.name in depends or len(depends[self.name]) == 0:
            return None

        depends = depends[self.name][0]

        # Rewrite the dependency
        try:
            return str(BoolRewriter(self.rsf, depends, eval_to_module = eval_to_module).rewrite())
        except BoolParserException:
            return ""

    def has_depends(self):
        depends = self.rsf.depends()

        if not self.name in depends or len(depends[self.name]) == 0:
            return False
        return True

    def __unicode__(self):
        return u"<Option %s, tri: %s>" % (self.name, str(self.tristate()))

class Choice(Option):
    def __init__(self, rsf, name, tristate, required):
        Option.__init__(self, rsf, name, tristate, False)

        ## In case of no dependencies::
        # Boolean tristates are always on, when choice is tristate, we
        # have a ChoiceMeta option in the symbol dict
        self.set_omnipresent(not tristate and not self.has_depends())

        self._required = required

    def required(self):
        return self._required

    def insert_forward_references(self):
        """Insert dependencies SYMBOL -> CHOICE"""
        items = self.rsf.collect("ChoiceItem", 1, True)
        deps = {}
        own_items = []
        deps[self.rsf.symbol(self.name)] = []

        if self.tristate():
            deps[self.rsf.symbol_module(self.name)] = []
            # If we are tristate there is an ALWAYS_ON item
            # CHOICE_%d_META.
            # This is also a dependency of both items.
            deps[self.symbol()].append("%s_META" % self.symbol())
            deps[self.symbol_module()].append("%s_META" % self.symbol())


        if self.name in items:
            for [symbol] in items[self.name]:
                if symbol in self.rsf.options():
                    own_items.append(symbol)
                    deps[self.rsf.symbol(symbol)] = [self.rsf.symbol(self.name)]
                    if self.tristate():
                        # If the choice is tristate the CHOICE_MODULE
                        # implies, that no option from the choice is
                        # selected as builtin unit
                        deps[self.rsf.symbol_module(self.name)].append("!" + self.rsf.symbol(symbol))
                        opt = self.rsf.options()[symbol]
                        if opt.tristate():
                            deps[self.rsf.symbol_module(symbol)] = [self.rsf.symbol_module(self.name)]


        or_clause = []
        and_clause_count = len(own_items)
        if not self._required:
            # If we have an optional choice, also no item can be
            # selected. So we add an and clause where all items are negated.
            and_clause_count += 1
        for x in range(0, and_clause_count):
            and_clause = []
            for y in range(0, len(own_items)):
                if x == y:
                    and_clause.append(self.rsf.symbol(own_items[y]))
                else:
                    and_clause.append("!" + self.rsf.symbol(own_items[y]))
            or_clause.append(" && ".join(and_clause))
        deps[self.rsf.symbol(self.name)].extend([ "((" + ") || (".join(or_clause) + "))"])

        return deps

class ChoiceMeta(Option):
    def __init__(self, choice):
        self.choice = choice
        Option.__init__(self, choice.rsf, choice.name + "_META", tristate=False, omnipresent=False)
        self.set_omnipresent(not choice.has_depends())

    def dependency(self, eval_to_module = True):
        return "((%s && !%s_MODULE) || (!%s && %s_MODULE))" % \
               tuple([self.choice.name] * 4)
