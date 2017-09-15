
# Variables
NAME=SplunkforPaloAltoNetworks

TARGET_ARCHIVE_DIR?=..
TARGET_WORKING_DIR?=working
RANDINT?=$(shell echo `awk -v min=10000 -v max=99999 'BEGIN{srand(); print int(min+rand()*(max-min+1))}'`)

BETA_FORMAT?=zip
BETA_BRANCH?=develop

CURRENT_VERSION?=$(shell echo `sed -n -e 's/^version *= *\(.*\)/\1/p' default/app.conf`)

bumpversion: BUMP?=patch
bumpversion: CURRENT_BUILD?=$(shell echo `sed -n -e 's/^build *= *\(.*\)/\1/p' default/app.conf`)
bumpversion: BUILD=$(shell echo $$(( $(CURRENT_BUILD) + 1 )))

build:
	git archive master | tar -x -C $(TARGET_WORKING_DIR)
	find $(TARGET_WORKING_DIR) -type f -name ".*" -exec rm {} \;
	rm $(TARGET_WORKING_DIR)/$(NAME)/Makefile
	rm $(TARGET_WORKING_DIR)/$(NAME)/bin/lib/pan-python/doc/Makefile
	tar czvf -C $(TARGET_WORKING_DIR) $(TARGET_ARCHIVE_DIR)/$(NAME)-$(CURRENT_VERSION).spl $(NAME)

buildbeta:
	git archive --format $(BETA_FORMAT) --prefix=$(NAME)/ --output $(TARGET_ARCHIVE_DIR)/$(NAME)-$(CURRENT_VERSION).$(BETA_FORMAT) $(BETA_BRANCH)

bumpversion:
	sed -i '' -E 's/build = .*/build = $(BUILD)/' default/app.conf
	bumpversion --verbose --allow-dirty --current-version $(CURRENT_VERSION) $(BUMP) default/app.conf

