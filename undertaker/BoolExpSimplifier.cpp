/*
 * boolean framework for undertaker and satyr
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

#include "bool.h"
#include "BoolExpSimplifier.h"

void kconfig::BoolExpSimplifier::visit(BoolExp *) {
    this->result = NULL;
}

void kconfig::BoolExpSimplifier::visit(BoolExpNot *) {
    BoolExp *node = static_cast<BoolExp *>(this->right);
    BoolExpConst *constant = dynamic_cast<BoolExpConst*>(node);
    if (constant) {
        bool v = !constant->value;

        BoolExp *ret = B_CONST(v);
        this->result = ret;
        return;
    }

    BoolExpNot *notExpr = dynamic_cast<BoolExpNot*>(node);
    if (notExpr) {
        BoolExp *x = notExpr->right;
        this->result = x;
        return;
    }

    this->result = new BoolExpNot(node);
}

void kconfig::BoolExpSimplifier::visit(BoolExpAnd *) {
    BoolExp *sr = static_cast<BoolExp *>(this->right);
    BoolExp *sl = static_cast<BoolExp *>(this->left);
    BoolExpConst *right = dynamic_cast<BoolExpConst*>(sr);
    BoolExpConst *left = dynamic_cast<BoolExpConst*>(sl);

    if (left != NULL || right != NULL) {
        BoolExpConst *c = left ? left : right;
        BoolExp *var = left ? sr : sl;
        if (c->value == true) {
            this->result = var;
            return;
        }
        else {
            this->result = c;            //0
            return;
        }
    }
    {
        // X && X
        BoolExpVar *right = dynamic_cast<BoolExpVar*>(sr);
        BoolExpVar *left = dynamic_cast<BoolExpVar*>(sl);
        if (left != NULL && right != NULL) {
            if (right->equals(left)) {
                //delete right;
                this->result = left;
                return;
            }
        }
    }
    {
        // X && !X
        BoolExpVar *right = dynamic_cast<BoolExpVar*>(sr);
        BoolExpVar *left = dynamic_cast<BoolExpVar*>(sl);
        if (left != NULL || right != NULL) {
            BoolExpVar *var = left ? left : right;
            BoolExp *other = left ? sr : sl;
            BoolExpNot *inverse = dynamic_cast<BoolExpNot*>(other);
            //TODO replace with equal()
            if (inverse && inverse->right->equals(var)) {
                 this->result = B_CONST(false);
                 return;
            }
        }
    }

    this->result = B_AND(sl, sr);
}

void kconfig::BoolExpSimplifier::visit(BoolExpOr *) {
    BoolExp *sr = static_cast<BoolExp *>(this->right);
    BoolExp *sl = static_cast<BoolExp *>(this->left);
    {
        BoolExpConst *right = dynamic_cast<BoolExpConst*>(sr);
        BoolExpConst *left = dynamic_cast<BoolExpConst*>(sl);

        // x || 0; X||1
        if (left != NULL || right != NULL) {
            BoolExpConst *c = left ? left : right;
            BoolExp *var = left ? sr : sl;
            if (c->value == false) {
                this->result = var;
                 return;
            }
            else {
                 this->result = c;        //1
                 return;
            }
        }
    }
    {
        // X || !X
        BoolExpVar *right = dynamic_cast<BoolExpVar*>(sr);
        BoolExpVar *left = dynamic_cast<BoolExpVar*>(sl);
        if (left != NULL || right != NULL) {
            BoolExpVar *var = left ? left : right;
            BoolExp *other = left ? sr : sl;
            BoolExpNot *inverse = dynamic_cast<BoolExpNot*>(other);
            // TODO replace with equal()
            if (inverse && inverse->right->equals(var)) {
                 this->result = B_CONST(true);
                 return;
            }
        }
    }
    {
        // X || X
        BoolExpVar *right = dynamic_cast<BoolExpVar*>(sr);
        BoolExpVar *left = dynamic_cast<BoolExpVar*>(sl);
        if (left != NULL && right != NULL) {
            if (right->equals(left)) {
                //delete right;
                 this->result = left;
                 return;
            }
        }
    }
    {
        // X || X
        BoolExpVar *right = dynamic_cast<BoolExpVar*>(sr);
        BoolExpVar *left = dynamic_cast<BoolExpVar*>(sl);
        if (left != NULL && right != NULL) {
            if (right->equals(left)) {
                 this->result = left;
                 return;
            }
        }
    }

    this->result = B_OR(sl, sr);
}

void kconfig::BoolExpSimplifier::visit(BoolExpImpl *) {
    BoolExp *sr = static_cast<BoolExp *>(this->right);
    BoolExp *sl = static_cast<BoolExp *>(this->left);
    {
        BoolExpConst *right = dynamic_cast<BoolExpConst*>(sr);

        // x -> 1;
        if (right != NULL && right->value == true) {
            //delete sr;
            //delete sl;
            this->result = B_CONST(true);
            return;
        }
        // x-> 0
        if (right != NULL && right->value == false) {
            //delete sr;
            BoolExp *notsl = B_NOT(sl);
            BoolExp *notsl_simpl =  notsl->simplify();
            //delete notsl;
            this->result = notsl_simpl;
            return;
        }
    }

    this->result = new BoolExpImpl(sl, sr);
}

void kconfig::BoolExpSimplifier::visit(BoolExpEq *) {
    BoolExp *sr = static_cast<BoolExp *>(this->right);
    BoolExp *sl = static_cast<BoolExp *>(this->left);
    this->result = new BoolExpEq(sl, sr);
}

void kconfig::BoolExpSimplifier::visit(BoolExpAny *) {
    this->result = NULL;
}

void kconfig::BoolExpSimplifier::visit(BoolExpCall *) {
    this->result = NULL;
}

void kconfig::BoolExpSimplifier::visit(BoolExpConst *e) {
    this->result = new BoolExpConst(*e);
}

void kconfig::BoolExpSimplifier::visit(BoolExpVar *e) {
    this->result = new BoolExpVar(*e);
}
