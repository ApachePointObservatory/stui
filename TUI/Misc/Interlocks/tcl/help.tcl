#
# Provide help with the MCP windows
#
#
# Display a help string in a toplevel window
#
proc give_help {title text} {
   #
   # First find/create the display window
   #
   if [winfo exists .mcp_help] {
      wm deiconify .mcp_help
      raise .mcp_help
   } else {
      toplevel .mcp_help -class Dialog
      wm title .mcp_help "MCP Help"

      label .mcp_help.title
      pack .mcp_help.title
      #
      # Use a text not a label so that cut-and-paste works
      #
      text .mcp_help.text -wrap word -relief flat
      pack .mcp_help.text
   }
   #
   # Time to set the content
   #
   .mcp_help.title configure -text $title
   if {$title == "deleteme"} {
      echo RHL "This shouldn't happen (deleteme) $title"
      traceback
   }
   #
   # Insert that text
   #
   .mcp_help.text delete 1.0 end
   .mcp_help.text insert end $text
   
   set width [string length $text]
   if {$width < 50} {
      set width 50
   } elseif {$width > 80} {
      set width 80
   }
   set lines [split $text "\n"]
   
   .mcp_help.text configure -height [llength $lines] -width $width
}

###############################################################################
#
# Provide some help on the requested topic
#
proc mcp_help {what} {
   global mcp_main

   set help_symbols \
"The red or green symbols are the values of the interlocks (green: 0, red: 1),
and the possible shapes mean:
   circle  : A value from the MCP (e.g. n_wind_stop)
   square  : A logical expression whose value is returned by the MCP
   diamond : A value calculated by the PLC whose value is not available
             to us. On the otherhand, we do have the values used to
             calculate it, e.g. voltages and currents so these are used,
             with coefficients that may or may not be correct.

You may ignore an interlock bit (and all of its consequences) by clicking
with the middle mouse button; click again to turn it back on.

The colours used are \$colors(led_bad), \$colors(led_ok), and \$colors(led_ignore).
"

   switch $what {
      "interlock_logic" {
	 set title "MCP Interlock Logic"
	 set text \
"
$help_symbols

You can left-click on these symbols to learn more about them; if it's a
logical expression (square) the logic tree will be popped up;
otherwise a window describing the field appears. The right button
always leads to this descriptive window.  If you control-left-click,
a popup will appear telling you which PLC bits (if any) are responsible
for the interlock being inhibited. The usual button bindings work.

Interlock fields that are present in our logic diagrams but not the
MCP packets are shown in black (and are assumed to be 0).

If you know the name of an interlock (e.g. alt_lvdt_error) you can enter it
in the \"Show\" box, and we'll tell you what we know; either a description,
or a logic diagram.
"
      }
      ".mcp_interlocks" {
	 set title "All MCP Interlocks"
	 set text \
"
This is a list of all fields provided in the MCP's UDP packets, and
also some derived quantities that the PLC uses. Fields named \"rack_n_grp\"
\"spare\", or \"undefined\" are not shown.

$help_symbols

You can left-click on the symbols or names to learn more about them.
If it's a logical expression (square) the logic tree will be popped up;
otherwise a window describing the field appears. The right button always
leads to this descriptive window.

The check button checks the logic of the interlock system; inconsistencies
are shown in red, and interlocks that are not relevent to the toplevel ones
displayed by key_interlocks are shown with a gray background.

You can choose to sort the interlocks by their name, or by the class that
they belong to (and by name within that class). This takes some time.

You can use the \"grep\" button to provide a regular expression
specifying the interlocks that you want to see; e.g. \"az\" or \"_in\$\"

If there are interlocks in the logic diagrams that the MCP isn't broadcasting,
a second window is popped up to list them.
"
      }
      $mcp_main {
	 set title "Main MCP Interlock Panel"
	 set text \
"
The bottons such as \"rotator\" across the top of the window are the highest
level interlocks; if green (\$colors(led_ok)) they are free to move, otherwise
they're red (\$colors(led_bad)). If you left-click on one of these an
interlock logic diagram for that permission is displayed.  Ctrl-leftclick
pops up a window that gives the root causes of the problem.

Below this permissions display are a set of buttons giving the status of
various mechanical and electrical interlocks; the left-hand set have both
on and off sensors, and can be caught between positions, while the right-hand
set are simple switches. A left-click on one of the two-position interlocks
describes the \"on\" state, a right-click the \"off\" state. Only the left
button is active for the single state interlocks such as stop buttons.

In the bottom left there's a small panel which provides access to the
instrument change window.  You can raise it (if it exists) by clicking
on the title \"Instrument Changes\".

At the bottom of the window are a set of control buttons:
   Panels         Pop-up windows with the status of interlocks and other items
   Updates        Control the updating of information from the MCP, including
		  reading a TPM interlocks dump file.
   Reload Logic   Reload the file which describes the interlock logic
   Help           Display this window
"
      }
      default {
	 set title "????"
	 set text "I don't know anything about $what"
      }
   }

   give_help $title $text
}
