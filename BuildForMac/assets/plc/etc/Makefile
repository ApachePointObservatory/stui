SHELL = /bin/sh

default:
	@echo Please invoke this makefile using sdssmake. >&2
	@exit 1

#
# Definitions of PLC bit fields
#
SDSS_CSV = $(PLC_DIR)/etc/sdss.csv $(PLC_DIR)/etc/extra.csv

all: dervish.tcl documentation.tcl constants.tcl read_tpm_dump.tcl ../src/printout.c
	@echo ""

#
# data_collection.h is built when include/ is built.
#
 ../include/data_collection.h:
	@if [ ! -e  ../include/data_collection.h ]; then \
		echo include/data_collection.h does not exist. make has to process include dir first. \
		exit 1; \
	fi

../src/printout.c constants.tcl : dervish.tcl parse.tcl ../include/data_collection.h
	echo "source parse.tcl; \
				parse_h_file ../include/data_collection.h; \
				write_printout_c ../src/printout.c; \
				write_axis_stat constants.tcl" | tclsh
	chmod 444 constants.tcl
#
# Generate documentation/bitfield definitions from a .csv file
#
documentation.tcl: $(PLC_DIR)/bin/read-csv $(SDSS_CSV)
	$(PLC_DIR)/bin/read-csv -d interlockDescriptions $(SDSS_CSV) > documentation.tcl; \
   chmod 444 documentation.tcl
dervish.tcl : dervish.tcl.skl $(PLC_DIR)/bin/read-csv $(SDSS_CSV)
	$(PLC_DIR)/bin/read-csv -p mcpData -s dervish.tcl.skl $(SDSS_CSV) > dervish.tcl; \
   chmod 444 dervish.tcl
read_tpm_dump.tcl : $(PLC_DIR)/bin/read-csv $(SDSS_CSV)
	$(PLC_DIR)/bin/read-csv -t $(SDSS_CSV) > read_tpm_dump.tcl; \
   chmod 444 read_tpm_dump.tcl

install:
	@if [ "$(PLC_DIR)" = "" ]; then \
		echo You have not specified a destination directory >&2; \
		exit 1; \
	fi
	-@/bin/rm -rf $(PLC_DIR)/etc
	@mkdir        $(PLC_DIR)/etc
	@cp Makefile extra.csv sdss.csv *.tcl $(PLC_DIR)/etc

clean:
	- /bin/rm -fr *~ .*~ core *.bak *.orig *.old .\#* \#*\#
	rm -f dervish.tcl documentation.tcl constants.tcl read_tpm_dump.tcl
