#!/usr/local/bin/python
import Tkinter

# dict of event type: event name
eventDict = {
	 '2': 'KeyPress',
	 '3': 'KeyRelease',
	 '4': 'ButtonPress',
	 '5': 'ButtonRelease',
	 '6': 'Motion',
	 '7': 'Enter',
	 '8': 'Leave',
	 '9': 'FocusIn',
	'10': 'FocusOut',
	'12': 'Expose',
	'15': 'Visibility',
	'17': 'Destroy',
	'18': 'Unmap',
	'19': 'Map',
	'21': 'Reparent',
	'22': 'Configure',
	'24': 'Gravity',
	'26': 'Circulate',
	'28': 'Property',
	'32': 'Colormap',
	'36': 'Activate',
	'37': 'Deactivate',
}

root = Tkinter.Tk()

def reportEvent(evt):
	eventName = eventDict.get(evt.type, 'Unknown')
	rptList = [
		'\n\n%s\nEvent:' % (80*'=',),
		' type=%r (%r' % (evt.type, eventName,),
		'\nserial=%r' % (evt.serial,),
		'time=%r' % (evt.time,),
		'widget=%r' % (evt.widget,),
		'\nx=%r  y=%r' % (evt.x, evt.y),
		'x_root=%r' % (evt.x_root,),
		'y_root=%r' % (evt.y_root,),
		'\nnum=%r' % (evt.num,),
		'char=%r' % (evt.char,),
		'keysym=%r' % (evt.keysym,),
		'keysym_num=%r' % (evt.keysym_num,),
		'delta=%r' % (evt.delta,),
		'\nheight=%r' % (evt.height,),
		'width=%r' % (evt.width,),
	]

	#### some event types don't have these attributes 
	try:
		rptList.append(
			'focus=%s' % (evt.focus)
		)
	except:
		pass
	try:
		rptList.append(
			'send_event=%s' % (evt.send_event)
		)
	except:
		pass
	
	logWdg.yview("end")
	logWdg.insert("end", '; '.join(rptList))
	
userLabel = Tkinter.Label(root, text="Type here:")
userEntry  = Tkinter.Entry(root, width=10, takefocus=1, highlightthickness=2)
logWdg = Tkinter.Text(root)

for eventName in eventDict.values():
	userLabel.bind('<%s>' % eventName, reportEvent)
	userEntry.bind('<%s>' % eventName, reportEvent)

userLabel.grid(row=0, column=0)
userEntry.grid(row=0, column=1, sticky='ew')
logWdg.grid(row=1, column=0, columnspan=2, sticky="news")
root.rowconfigure(1, weight=1)
root.columnconfigure(1, weight=1)

userEntry.focus_set()
root.mainloop()
