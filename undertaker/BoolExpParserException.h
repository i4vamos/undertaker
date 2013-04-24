/*
 *   boolean framework for undertaker and satyr
 *
 * Copyright (C) 2012 Ralf Hackner <rh@ralf-hackner.de>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 */

#ifndef KCONFIG_BOOL_EXP_PARSER_EXCEPTION_H
#define KCONFIG_BOOL_EXP_PARSER_EXCEPTION_H

#include <stdexcept>

struct BoolExpParserException : public std::runtime_error {
    BoolExpParserException(const char *s) : runtime_error(s) {}
    BoolExpParserException(std::string s) : runtime_error(s.c_str()) {}
};
#endif
