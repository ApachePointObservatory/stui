#########################################################
#  Tcl program to parse C structure definition
#  Originally by Dennis Nicklaus nicklaus@fnal.gov
# 
#  Does a very simple parsing of a structure.
#  The whole structure must be defined in this one .h file.
#  Structures can be nested (e.g. one structure built up of 
#  several smaller structures.
#  The idea is, after "source"-ing this Tcl script, which
#  causes the parsing work to be done, then you call
#  proc pthem to generate the output you want, either:
#     a list of every field of the structure "exploded" so that each
#     substructure is also broken down.
#  or
#     the same list but including each field in a C printf statement
#     to print out the field value. Every field is printf'ed as an "int",
#     one value per line.
#
#  The output of pthem can be used as the input file to the ReadNames
#  procedure of the socket monitoring file sockmon.tcl

#  THIS IS NOT A FULL C COMPILER!!
#  It is  just a simple one-pass parser that is able to recognize
#  some simple C declarations/definitions.  It is pretty dumb, really.
#  It just does enough to get by for the example I had.

source "dervish.tcl"

proc parse_h_file {{fname ../mcp/data_collection.h}} {
   global C_types names2nums struct_contents
   #
   # C types that are acceptable (as a regexp)
   #
   set C_types "time_t|int|long|char|short|float|double"

   set numstructs 0
   set struct_name_is_next 0
   set nextword_sname 0
   set structname_comes_at_end 0
   set ignore_things 0
   set bitfield 0;			# are we processing a bitfield element?
   set nbit 0;				# current width of bitfield
   set type_modifier ""; set type ""
   set parselevel OUTSIDE
   set PRETTY_END   "+*/"
   
   foreach s "names2nums struct_contents" {
      if [info exists $s] {
	 unset $s
      }
   }


   # Now begins the fun of the processing.
   # The main loop of the parsing works by examining each word
   # and having some expectation of what the next work might be
   # based on a few state variables, including "parselevel".
   
   echo "Parsing $fname"
   set in [open $fname]

   set body [read $in]
   # The first thing we do is to make sure the important tokens
   # (brackets, semicolons,...) have spaces around them.
   # There are probably other things that need to be space separated
   # that aren't covered by this simple regexp, but the file I've
   # dealt with so far hasn't needed anything more than this.
   regsub -all {([;:{}])} $body { \1 } body
   regsub -all {([^ ])(\*/)} $body {\1 \2} body
   #
   # Remove all extern declarations
   #
   regsub -all {extern [^;]*;} $body "" body   
   
   foreach word [split $body] {
    if {[string length $word] > 0} {
      switch -exact $parselevel {
	COMMENT {
	  if {[string compare "*/" $word] == 0} {
	    set parselevel $parselevel_previous
	  }
	}
	PRETTYNAME {
	  if {[string compare $PRETTY_END $word] == 0} {
	    set parselevel $parselevel_previous
	    lappend struct_prettynames($recent_structnum) $prettyname_collector
	    unset prettyname_collector
	  } else {
		lappend prettyname_collector $word
	  }
	}
	OUTSIDE {
	  if {[string compare "/*" $word] == 0} {
	    set parselevel_previous $parselevel
	    set parselevel COMMENT
	  } else {
	    if $struct_name_is_next {
  	      set names2nums($word) $numstructs
  	      set recent_structnum $numstructs
	      incr numstructs
	      set struct_name_is_next 0
	      set parselevel INSIDE
	    } else {
	      if {[string compare "typedef" $word] == 0} {
		set structname_comes_at_end 1
  	        set recent_structnum $numstructs
	      } elseif {[string compare "struct" $word] == 0} {
		if $structname_comes_at_end {
		  set struct_name_is_next 0
	          set parselevel INSIDE
		} else {
		  set struct_name_is_next 1
		}
	      } elseif {[string compare "#define" $word] == 0} {
		set ignore_things 2
		set parselevel_previous $parselevel
		set parselevel IGNORE
	      }
	    }
	  }
	}
	IGNORE {
	  incr ignore_things -1
	  if {$ignore_things <= 0} {
	    set parselevel $parselevel_previous
	  }
	}
	INSIDE {
	  if {[string compare "/*" $word] == 0} {
	    set parselevel_previous $parselevel
	    set parselevel COMMENT
	  } elseif $struct_name_is_next {
	    set names2nums($word) $numstructs
	    set recent_structnum $numstructs
	    incr numstructs
	    set struct_name_is_next 0
	    set structname_comes_at_end 0
	    set parselevel OUTSIDE
	  } elseif {$nextword_sname} {
	     set type $word
	     set nextword_sname 0
	  } else {
	     #
	     # This test cannot go in the switch as $C_types isn't expanded,
	     # and the agony and illegiblity of getting the quoting right
	     # just isn't worth it
	     #
	     if [regexp "^($C_types)$" $word] {
		set type $word
	     } else {
		switch -regexp $word {
		   "^\}$" {
		      if $structname_comes_at_end {
			 set struct_name_is_next 1
		      } else {
			 set parselevel OUTSIDE
		      }
		   }
		   {^#define$} {
		      set ignore_things 2
		      set parselevel_previous $parselevel
		      set parselevel IGNORE
		   }
		   "^\{$" {
		      continue
		   }
		   "^/\\*\\+$" {		# Unused?
		      set parselevel_previous $parselevel
		      set parselevel PRETTYNAME
		   }
		   {^(un)?signed$} {
		      set type_modifier $word
		   }
		   {;} {
		      if {$type == ""} {
			 set type "int"
		      }
		      if {$type_modifier != ""} {
			 set type "${type_modifier}_$type"
		      }
		      if {$nbit > 0} {
			 append type ":$nbit"
		      }
		      
		      lappend struct_contents($recent_structnum) \
			  $type $variable_name
		      
		      set type_modifier ""; set type ""; set nbit 0
		      set variable_name ""
		   }
		   {:} {
		      set bitfield 1
		   }
		   {^[1-3]?[0-9]$} {
		      if $bitfield {
			 set nbit $word
		      } else {
			 error "Saw $word when I expected a bitfield width"
		      }
		   }
		   {^struct$} {set nextword_sname 1 }
		   {.*} {
		      if {$type_modifier == "" && $type == ""} {
			 set type $word
		      } else {
			 set variable_name $word;
		      }
		   }
		}
	     }
	  }
	}
      }
    }
  }
}

#  Print out param.names or printout.c files to be used with sockmon.tcl
#
#  Note that you don't pass a filename, you pass an already open file
# descriptor, e.g. something like $A where you did set A [open param.names w]

proc pthem { fd cstruct sname {do_structs 1} {prefix ""}} {
   global C_types names2nums struct_contents

   set ps $names2nums($sname)
   set separator ":"
   #
   # If the struct is actually a collection of bitfields, figure
   # out how wide it is
   #
   set width 0; set nbit 0
   foreach var $struct_contents($ps) {
      if [regexp "^((un)?signed_)?($C_types)(:(\[0-9\]+))$" $var \
	      foo goo hoo type joo nbit] {
	 incr width $nbit
      }
   }
   
   if {$width == 0} {
      ;					# OK
   } elseif {$width <= 8} {
      set width 8
   } elseif {$width <= 16} {
      set width 16
   } elseif {$width <= 32} {
      set width 32
   } elseif {$width <= 64} {
      set width 64
   }
   
   if [regexp {^(0|16|32|64)$} $width] {
      set nbyte [expr $width/8]
   } else {
      error "I cannot handle fieldwidths of $width ($ps $var)"
   }
   if {$nbyte == 0} {
      set swap ""
   } else {
      regsub -all "$separator" $prefix "." c_var
      set c_var "$cstruct.$c_var"

      set swap "   flip_bits_in_bytes(&$c_var, $nbyte);"
   }
   #
   # Now deal with the data elements themselves
   #
   set structp 0
   set skip_element 0;			# skip this element?
   foreach var $struct_contents($ps) {
      if [regexp "^((un)?signed_)?($C_types)(:(\[0-9\]+))?$" $var \
	      foo goo hoo type bitfield nbit] {
	 continue;			# type information
      } elseif {$var == ""} {
	 continue;			# anonymous bitfield
      }
      
      if {!$do_structs && [info exists names2nums($var)]} {
	 set skip_element 1
	 continue
      } elseif {$skip_element || [regexp {\[[0-9a-zA-Z_]+\]$} $var] ||
		[regexp {undefined} $var]} {
	 set skip_element 0
	 continue;
      }

      if {$structp != 0} {
	 if {$prefix == ""} {
	    set ps ""
	 } else {
	    set ps "$prefix$separator"
	 }

	 pthem $fd $cstruct $structp $do_structs "$ps$var"
	 set structp 0
      } else {
	 if {[info exists names2nums($var)]} {
	    set structp $var
	 } else {
	    #
	    # We could only generate this code if we know we're on
	    # a little endian machine (using shEndian), but it seems
	    # safer to generate code that will run on both machine types
	    #
	    if ![info exists type] {
	       error "No type information is available for $var"
	    }

	    switch $type {
	       "char" {
		  set nbyte 1
		  set fmt "%d"
	       }
	       "short" {
		  set nbyte 2
		  set fmt "%d"
	       }
	       "int" {
		  set nbyte 4
		  set fmt "%d"
	       }
	       "long" {
		  set nbyte 4
		  set fmt "%ld"
	       }
	       "time_t" {
		  set nbyte 4
		  set fmt "%ld"
	       }
	       "float" {
		  set nbyte 4
		  set fmt "%f"
	       }
	       "double" {
		  set nbyte 8
		  set fmt "%lf"
	       }
	       "default" {
		  error "Unknown type: $type"
	       }
	    }
	    #
	    # Adjust that variable name to work in both C and TCL
	    #
	    set tcl_var $var

	    if {$prefix != ""} {
	       set var $prefix$separator$var
	    }
	    
	    regsub -all "$separator" $var "." c_var
	    set c_var "$cstruct.$c_var"

	    if {$nbyte > 1} {
	       if {$bitfield == ""} {
		  set swap "   swab${nbyte}(&$c_var, $nbyte);"
	       }
	       if {$swap != ""} {
		  puts $fd "#if defined(SDSS_LITTLE_ENDIAN)"
		  puts $fd $swap
		  puts $fd "#endif"
		  set swap ""
	       }
	    }
	    
	    puts $fd "\
 \  sprintf(bptr,\"$tcl_var $fmt\\n\",
                 $c_var);
   bptr += strlen(bptr);
"
	    set structp 0
	 }
      }
   }
}

proc write_printout_c {{file ""} {cbase inbuf}} {
   if {$file == ""} {
      set fd stdout
   } else {
      echo "(Over)writing $file"
   
      if [catch {set fd [open $file w]} msg] {
	 error "I cannot open $file for write"
      }
   }
   
   pthem $fd (*$cbase)          "SDSS_FRAME" 0
   pthem $fd $cbase->inst       "IL"
   pthem $fd $cbase->status     "AB_SLC500"

   if {$fd != "stdout"} {
      close $fd
   }
}

#
# Print out the values corresponding to the fields in AXIS_STAT
#
proc write_axis_stat {{file ""}} {
   global struct_contents names2nums

   if {$file == ""} {
      set fd stdout
   } else {
      echo "(Over)writing $file"
   
      if [catch {set fd [open $file w]} msg] {
	 error "I cannot open $file for write"
      }
   }

   set list $struct_contents($names2nums(AXIS_STAT))

   puts $fd "array set AXIS_STAT \[list \\"

   set val 1
   loop i [expr [llength $list]-1] 0 -2 {
      set name [lindex $list $i]
      regexp {:([0-9]+)$} [lindex $list [expr $i-1]] foo width
      if {$name != ""} {
	 puts $fd [format "   0x%-10x %s \\" $val $name]
      }
      set val [expr $val<<$width]
   }

   puts $fd "\]"

   if {$fd != "stdout"} {
      close $fd
   }
}
