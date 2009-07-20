SHELL = /bin/sh
#
# Definitions of PLC bit fields
#
SDSS_CSV = $(PLC_DIR)/etc/sdss.csv $(PLC_DIR)/etc/extra.csv

all: documentation.tcl constants.tcl read_tpm_dump.tcl
	@echo ""
#
# Machine generate stuff from data_collection.h
#
constants.tcl : dervish.tcl parse.tcl $(PLC_DIR)/include/data_collection.h
	echo "source parse.tcl; \
				parse_h_file $(PLC_DIR)/include/data_collection.h; \
				write_axis_stat constants.tcl" | tclsh
#
# Generate documentation/bitfield definitions from a .csv file
#
documentation.tcl : $(PLC_DIR)/bin/read-csv $(SDSS_CSV)
	$(PLC_DIR)/bin/read-csv -d interlockDescriptions $(SDSS_CSV) > documentation.tcl
dervish.tcl : dervish.tcl.skl $(PLC_DIR)/bin/read-csv $(SDSS_CSV)
	$(PLC_DIR)/bin/read-csv -p mcpData -s dervish.tcl.skl $(SDSS_CSV) > dervish.tcl
read_tpm_dump.tcl : $(PLC_DIR)/bin/read-csv $(SDSS_CSV)
	$(PLC_DIR)/bin/read-csv -t $(SDSS_CSV) > read_tpm_dump.tcl
#
# Install product
#
install : all
	@if [ "$(INTERLOCKS_DIR)" = "" ]; then \
		echo You have not specified a destination directory >&2; \
		exit 1; \
	fi     
	@ rm -rf $(INTERLOCKS_DIR)/etc/*
	cp *.tcl *.bit $(INTERLOCKS_DIR)/etc
#
clean :
	rm -f *~ core *.bak *.orig *.old .#* #*#
	rm -f dervish.tcl documentation.tcl constants.tcl read_tpm_dump.tcl
