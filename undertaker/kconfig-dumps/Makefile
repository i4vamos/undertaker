DUMPCONF=../../scripts/kconfig/dumpconf
KCONFIGDUMP=../../python/undertaker-kconfigdump
SATYR=../satyr
FM_DIR=../../fm/linux
FM_FILES=$(subst $(FM_DIR)/,,$(wildcard $(FM_DIR)/*.fm))
RSF_FILES=$(FM_FILES:.fm=.rsf)
MODELS=$(patsubst %.rsf,models/%.model,$(RSF_FILES))
CNF_MODELS=$(patsubst %.rsf,cnfmodels/%.cnf,$(RSF_FILES))
PATH:=$(CURDIR)/..:$(CURDIR)/../../scripts/kconfig:$(CURDIR):../../python:$(PATH)
export PATH

all: models cnfmodels

models: satyr dumpconf $(MODELS)

cnfmodels: satyr $(CNF_MODELS)

satyr: dumpconf
	$(MAKE) -C .. satyr

dumpconf:
	$(MAKE) -C ../.. scripts/kconfig/dumpconf

models/%.rsf: $(FM_DIR)/%.fm dumpconf
	@mkdir -p models
	ARCH=$* $(DUMPCONF) $(FM_DIR)/$*.fm | sort -u | grep -v '^#' > $@

models/%.model: models/%.rsf dumpconf
	$(KCONFIGDUMP) -m $* intermediate

cnfmodels/%.cnf: $(FM_DIR)/%.fm satyr dumpconf
	@mkdir -p cnfmodels
	ARCH=$* $(SATYR) $< -c $@

clean:
	rm -rf $(MODELS) $(CNF_MODELS)

FORCE:

.PHONY: FORCE all models cnfmodels dumpconf satyr
.SECONDARY:
