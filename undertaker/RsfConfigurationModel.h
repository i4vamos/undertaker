/*
 *   undertaker - analyze preprocessor blocks in code
 *
 * Copyright (C) 2009-2012 Reinhard Tartler <tartler@informatik.uni-erlangen.de>
 * Copyright (C) 2009-2011 Julio Sincero <Julio.Sincero@informatik.uni-erlangen.de>
 * Copyright (C) 2010-2011 Christian Dietrich <christian.dietrich@informatik.uni-erlangen.de>
 * Copyright (C) 2013-2014 Stefan Hengelein <stefan.hengelein@fau.de>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

// -*- mode: c++ -*-
#ifndef rsf_configuration_model_h__
#define rsf_configuration_model_h__

#include "ConfigurationModel.h"

class RsfReader;
class ItemRsfReader;


class RsfConfigurationModel : public ConfigurationModel {
    RsfReader *_model;
    ItemRsfReader *_rsf = nullptr;

    virtual void doIntersectPreprocess(std::set<std::string> &start_items,
                                       StringJoiner &sj) const final override;

    virtual void addMetaValue(const std::string &key, const std::string &val) const final override;

public:
    //! Loads the configuration model from file
    //! \param filename filepath to the model file. (NB: The basename is taken as architecture name.)
    RsfConfigurationModel(const std::string &filename);
    void extendWithInterestingItems(std::set<std::string> &) const;

    //! destructor
    virtual ~RsfConfigurationModel();
    //@{
    //! checks the type of a given symbol.
    //! @return false if not found
    virtual bool isBoolean(const std::string &)                    const final override;
    virtual bool isTristate(const std::string &)                   const final override;
    //@}

    //! returns the version identifier for the current model
    virtual const std::string getModelVersionIdentifier() const final override { return "rsf"; }

    //! returns the type of the given symbol
    //! Normalizes the given item so that passing with and without CONFIG_ prefix works.
    virtual std::string getType(const std::string &feature_name)   const final override;

    virtual bool containsSymbol(const std::string &symbol)         const final override;
    virtual const StringList *getMetaValue(const std::string &key) const final override;
};
#endif
