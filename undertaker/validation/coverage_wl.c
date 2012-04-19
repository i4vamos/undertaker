#if CONFIG_OFF

#endif

#if CONFIG_TO_BE_SET
// mind that this should reduce the coverage as else case will be ignored
#else

#endif

/*
 * check-name: whitelisting for coverage algorithms
 * check-command: undertaker -j coverage  $file -m coverage_wl.model -W coverage_wl.whitelist -B coverage_wl.blacklist ; cat coverage_wl.c.config1
 * check-output-start
I: loaded rsf model for coverage_wl.model
I: loaded 1 items to whitelist
I: loaded 1 items to blacklist
I: Using coverage_wl.model as primary model
I: 2 Items have been forcefully set
I: 1 Items have been forcefully unset
I: Entries in missingSet: 0
I: Removed 0 old configurations matching coverage_wl.c.config*
I: coverage_wl.c, Found Solutions: 1, Coverage: 2/4 blocks enabled (50%)
# FILE_coverage_wl.c=y
CONFIG_TO_BE_SET=y
# OFF=n
# THAT_IS_ALWAYS_ON=y
 * check-output-end
 */