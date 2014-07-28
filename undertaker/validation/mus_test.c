#ifdef CONFIG_BAR

#else

#endif

/*
 * check-name: MUS: check if mus is working and formula is constant
 * check-command: undertaker -vu -m file-presence-conditions.model $file ; cat mus_test.c.B1.kconfig.globally.dead.mus
 * check-output-start
I: Using file-presence-conditions as primary model
I: loaded rsf model for file-presence-conditions
I: creating mus_test.c.B0.kconfig.globally.undead
I: creating mus_test.c.B1.kconfig.globally.dead
I: creating mus_test.c.B1.kconfig.globally.dead.mus
ATTENTION: This formula _might_ be incomplete or even inconclusive!
Minimized Formula from:
p cnf 17 37
to
p cnf 17 18
(!B1 v !B0) ^ (B1) ^ (B0 v !CONFIG_BAR) ^ (B00) ^ (!B00 v FILE_mus_test.c) ^ (!CONFIG_FOO v CONFIG_BAR) ^ (!FILE_mus_test.c v CONFIG_FOO)
 * check-output-end
 */

