/*
 *   satyr - compiles KConfig files to boolean formulas
 *
 * Copyright (C) 2012 Ralf Hackner <rh@ralf-hackner.de>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, version 2.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef KCONFIG_CNF_H
#define KCONFIG_CNF_H

#include<map>
#include<string>
#include<iostream>


using namespace std;
namespace kconfig
{
    class CNF
    {
        public:
            virtual void readFromFile(istream &i) = 0;
            virtual void toFile(string &path)= 0;
            virtual int  getSymbolType(string &name) = 0;
            virtual void setSymbolType(string &sym, int type) = 0;
            virtual int getCNFVar(string &var) = 0;
            virtual void setCNFVar(string &var, int CNFVar) = 0;
            virtual string &getSymbolName(int CNFVar) = 0;
            virtual void pushVar(int v) = 0;
            virtual void pushVar(string  &v, bool val) = 0;
            virtual void pushClause(void) = 0;
            virtual void pushClause(int *c) = 0;
            virtual void pushAssumption(int v)= 0;
            virtual void pushAssumption(string &v,bool val)= 0;
            virtual void pushAssumption(const char *v,bool val)= 0;
            virtual bool checkSatisfiable(void)= 0;
            virtual void readAssumptionsFromFile(istream &i) = 0;
            virtual bool deref(int s) =0;
            virtual bool deref(string &s) =0;
            virtual std::map<string, int>::const_iterator getSymbolsItBegin() = 0;
            virtual std::map<string, int>::const_iterator getSymbolsItEnd() = 0;

    };
}
#endif