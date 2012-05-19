#if CONFIG_OFF
// CONFIG_OFF does not appear in model
// i.e. this block is dead
#else
// and this one is undead
#endif

#if CONFIG_TO_BE_SET
// mind that this should reduce the coverage as else case will be ignored
// i.e., this block is undead
#else
// this one is dead
#endif

/*
 * check-name: whitelisting for coverage algorithms
 * check-command: undertaker -j coverage $file -m coverage_wl.model -W coverage_wl.whitelist -B coverage_wl.blacklist ; cat coverage_wl.c.config1
 * check-output-start
I: loaded 1 items to blacklist
I: loaded 1 items to whitelist
I: loaded rsf model for coverage_wl.model
I: Using coverage_wl.model as primary model
I: 2 Items have been forcefully set
I: 1 Items have been forcefully unset
I: Entries in missingSet: 1
I: Removed 0 leftovers for coverage_wl.c
I: coverage_wl.c, Found Solutions: 1, Coverage: 3/5 blocks enabled (60%)
CONFIG_TO_BE_SET=y
CONFIG_THAT_IS_ALWAYS_ON=y
# CONFIG_OFF=n
# FILE_coverage_wl.c=y
 * check-output-end
 */
