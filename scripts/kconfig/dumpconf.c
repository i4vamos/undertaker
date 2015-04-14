/*
 * Copyright (C) 2009 Reinhard Tartler
 * Copyright (C) 2015 Stefan Hengelein <stefan.hengelein@fau.de>
 *
 * Released under the terms of the GNU GPL v2.0.
 */

#include <locale.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>

#define LKC_DIRECT_LINK
#include "lkc.h"


static int choice_count = 0;

// based on expr_print() from expr.c
void my_expr_print(struct expr *e, void *out, int prevtoken, char *choice) {
	if (!e) {
		fputs("y", out);
		return;
	}

	if (expr_compare_type(prevtoken, e->type) > 0)
		fputs("(", out);
	switch (e->type) {
	case E_SYMBOL:
		if (e->left.sym->name)
			fputs(e->left.sym->name, out);
		else if (choice)
			fputs(choice, out);
		else
			// if a symbol has a "depends on m" statement, kconfig will create an internal symbol
			// with flag SYMBOL_AUTO in the dependency, with no name. Ignore it.
			fputs("CADOS_IGNORED", out);
		break;
	case E_NOT:
		fputs("!", out);
		my_expr_print(e->left.expr, out, E_NOT, choice);
		break;
	case E_EQUAL:
		if (e->left.sym->name)
			fputs(e->left.sym->name, out);
		else
			fputs("<choice>", out);
		fputs("=", out);
		fputs(e->right.sym->name, out);
		break;
	case E_UNEQUAL:
		if (e->left.sym->name)
			fputs(e->left.sym->name, out);
		else
			fputs("<choice>", out);
		fputs("!=", out);
		fputs(e->right.sym->name, out);
		break;
	case E_OR:
		my_expr_print(e->left.expr, out, E_OR, choice);
		fputs(" || ", out);
		my_expr_print(e->right.expr, out, E_OR, choice);
		break;
	case E_AND:
		my_expr_print(e->left.expr, out, E_AND, choice);
		fputs(" && ", out);
		my_expr_print(e->right.expr, out, E_AND, choice);
		break;
	case E_LIST:
		fputs(e->right.sym->name, out);
		if (e->left.expr) {
			fputs(" ^ ", out);
			my_expr_print(e->left.expr, out, E_LIST, choice);
		}
		break;
	case E_RANGE:
		fprintf(out, "[%s %s]", e->left.sym->name, e->right.sym->name);
		break;
	default:
		fprintf(out, "<unknown type %d>", e->type);
		break;
	}
	if (expr_compare_type(prevtoken, e->type) > 0)
		fputs(")", out);
}

void my_print_symbol(FILE *out, struct menu *menu, char *choice) {
	struct symbol *sym = menu->sym;

	if (!sym_is_choice(sym)) {
		if (sym_is_choice_value(sym))
			fprintf(out, "ChoiceItem\t%s\t%s\n", sym->name, choice);

		fprintf(out, "Item\t%s\t%s\n", sym->name, sym_type_name(sym->type));
	}

	char itemname[50];
	int has_prompts = 0;
	struct property *prop;

	snprintf(itemname, sizeof itemname, "%s", sym->name ? sym->name : choice);

	if (menu->dep) {
		fprintf(out, "Depends\t%s\t\"", itemname);
		my_expr_print(menu->dep, out, E_NONE, choice);
		fprintf(out, "\"\n");
	}

	for_all_prompts(sym, prop)
		has_prompts++;

	fprintf(out, "HasPrompts\t%s\t%d\n", itemname, has_prompts);

	for_all_properties(sym, prop, P_DEFAULT) {
		fprintf(out, "Default\t%s\t\"", itemname);
		my_expr_print(prop->expr, out, E_NONE, choice);
		fprintf(out, "\"\t\"");
		my_expr_print(prop->visible.expr, out, E_NONE, choice);
		fprintf(out, "\"\n");
	}
	for_all_properties(sym, prop, P_SELECT) {
		fprintf(out, "ItemSelects\t%s\t\"", itemname);
		my_expr_print(prop->expr, out, E_NONE, choice);
		fprintf(out, "\"\t\"");
		my_expr_print(prop->visible.expr, out, E_NONE, choice);
		fprintf(out, "\"\n");
	}
	fprintf(out, "Definition\t%s\t\"%s:%d\"\n", itemname, menu->file->name, menu->lineno);

	if (sym_is_choice_value(sym))
		fputs("#choice value\n", out);
}

void handleChoice(FILE *out, struct menu *menu);

void handleSymbol(FILE *out, struct menu *menu, char *choice) {
	struct menu *child;
	bool was_choice = false;
	if (menu->sym) {
		if (sym_is_choice(menu->sym)) {
			handleChoice(out, menu);
			was_choice = true;
		} else {
			my_print_symbol(out, menu, choice);
		}
	}
	if (!was_choice)
		for (child = menu->list; child; child = child->next)
			// non-choice-values have a dependency on a choice if they are defined within a
			// choice structure, thus we have to forward the choice argument
			handleSymbol(out, child, choice);
}

void handleChoice(FILE *out, struct menu *menu) {
	char buf[12];
	struct menu *child;

	fprintf(out, "#startchoice\n");
	choice_count++;

	snprintf(buf, sizeof buf, "CHOICE_%d", choice_count);
	fprintf(out, "Choice\t%s", buf);

	// optional, i.e. all items can be deselected
	if (sym_is_optional(menu->sym))
		fprintf(out, "\toptional");
	else
		fprintf(out, "\trequired");

	if (menu->sym->type & S_TRISTATE)
		fprintf(out, "\ttristate");
	else
		fprintf(out, "\tboolean");

	fprintf(out, "\n");

	my_print_symbol(out, menu, buf);

	for (child = menu->list; child; child = child->next)
		handleSymbol(out, child, buf);

	fprintf(out, "#endchoice\t%s\n", buf);
}

void myconfdump(FILE *out) {
	struct menu *child;
	for (child = &rootmenu; child; child = child->next)
		handleSymbol(out, child, NULL);
}

int main(int ac, char **av) {
	struct stat tmpstat;
	char *arch = getenv("ARCH");

	setlocale(LC_ALL, "");
	bindtextdomain(PACKAGE, LOCALEDIR);
	textdomain(PACKAGE);

	if (stat(av[1], &tmpstat) != 0) {
		fprintf(stderr, "could not open %s\n", av[1]);
		exit(EXIT_FAILURE);
	}

	if (!arch) {
		fputs("setting arch to default: x86\n", stderr);
		arch = "x86";
		setenv("ARCH", arch, 1);
	}
	fprintf(stderr, "using arch %s\n", arch);
	setenv("KERNELVERSION", "2.6.30-vamos", 1);
	conf_parse(av[1]);
	myconfdump(stdout);
	return EXIT_SUCCESS;
}
