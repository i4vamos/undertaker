#ifdef CONFIG_TOPLEVEL_A
WITHIN TOPLEVEL_A
#ifdef CONFIG_LEVEL_A_B
WITHIN A AND B
#endif 
WITHIN A
#endif

#ifdef CONFIG_TOPLEVEL_C
WITHIN TOPLEVEL_C
#ifdef CONFIG_LEVEL_C_B
WITHIN C AND B
#endif 
WITHIN C
#else
OUT OF C
#endif

No CPP Precond
/*
 * check-name: calculate block preconditions without model
 * check-command: undertaker -j blockpc $file:12
 * check-output-start
I: Block B3 | Defect: no | Global: 0
B3
&& ( B2 <-> CONFIG_TOPLEVEL_C )
&& ( B3 <-> B2 && CONFIG_LEVEL_C_B )
&& B00
 * check-output-end
 */
