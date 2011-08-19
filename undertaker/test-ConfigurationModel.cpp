/*
 *   undertaker - analyze preprocessor blocks in code
 *
 * Copyright (C) 2011 Reinhard Tartler <tartler@informatik.uni-erlangen.de>
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

#include "ModelContainer.h"

#include <check.h>


START_TEST(getTypes) {
    ConfigurationModel *x86 = ModelContainer::loadModels("kconfig-dumps/models/x86.model");

    fail_unless(x86->inConfigurationSpace("CONFIG_64BIT"));
    fail_unless(x86->inConfigurationSpace("CONFIG_ACPI_BLACKLIST_YEAR"));
    fail_unless(x86->inConfigurationSpace("CONFIG_ARM"));
    fail_unless(x86->inConfigurationSpace("CONFIG_CGROUP_DEBUG"));
    fail_unless(x86->inConfigurationSpace("CONFIG_IKCONFIG"));
    
    fail_if(x86->isBoolean("ARM"), "ARM must not be present nor a boolean");
    fail_if(x86->isTristate("ARM"), "ARM must not be present nor a tristate");
    fail_if(x86->isBoolean("ACPI_BLACKLIST_YEAR"), "ACPI_BLACKLIST_YEAR must not be present nor a boolean");
    fail_if(x86->isTristate("ACPI_BLACKLIST_YEAR"), "ACPI_BLACKLIST_YEAR must not be present nor a tristate");

    fail_unless(x86->isBoolean("CGROUP_DEBUG"), "CGROUP_DEBUG should be a boolean option");
    fail_unless(x86->isBoolean("64BIT"), "64BIT should be a boolean option");
    fail_unless(x86->isTristate("IKCONFIG"), "IKCONFIG should be a tristate option");

} END_TEST;

Suite *cond_block_suite(void) {

    Suite *s  = suite_create("Suite");
    TCase *tc = tcase_create("ConfigurationModel");
    tcase_add_test(tc, getTypes);

    suite_add_tcase(s, tc);
    return s;
}

int main() {

    Suite *s = cond_block_suite();
    SRunner *sr = srunner_create(s);
    srunner_run_all(sr, CK_NORMAL);
    int number_failed = srunner_ntests_failed(sr);
    srunner_free(sr);

    return (number_failed == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}