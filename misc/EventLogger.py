#!/usr/local/bin/python
import Tkinter

eventList = { '2': 'KeyPress', '3': 'KeyRelease', '4': 'ButtonPress',
              '5': 'ButtonRelease', '6': 'Motion', '7': 'Enter',
              '8': 'Leave', '9': 'FocusIn', '10': 'FocusOut',
              '12': 'Expose', '15': 'Visibility', '17': 'Destroy',
              '18': 'Unmap', '19': 'Map', '21': 'Reparent',
              '22': 'Configure', '24': 'Gravity', '26': 'Circulate',
              '28': 'Property',  '32': 'Colormap','36': 'Activate',
              '37': 'Deactivate' }

root = Tkinter.Tk()

def reportEvent(event):
    rpt = '\n\n%s' % (80*'=')
    rpt = '%s\nEvent: type=%s (%s)' %  (rpt, event.type,
                                        eventList.get(event.type, 'Unknown'))
    rpt = '%s\nserial=%s' %            (rpt, event.serial)
    rpt = '%s  time=%s'   %            (rpt, event.time)
    rpt = '%s  widget=%s' %            (rpt, event.widget)
    rpt = '%s  height=%s' %            (rpt, event.height)
    rpt = '%s  width=%s' %             (rpt, event.width)
    rpt = '%s\nx=%d  y=%d'%            (rpt, event.x, event.y)
    rpt = '%s  x_root=%d' %            (rpt, event.x_root)
    rpt = '%s  y_root=%d' %            (rpt, event.y_root)
    rpt = '%s\nnum=%s' %               (rpt, event.num)
    rpt = '%s  keysym=%s' %            (rpt, event.keysym)
    rpt = '%s  ksNum=%s' %             (rpt, event.keysym_num)

    #### some event types don't have these attributes 
    try:
        rpt = '%s  focus=%s' %   (rpt, event.focus)
    except:
        pass
    try:
        rpt = '%s  send=%s' %    (rpt, event.send_event)
    except:
        pass
    
    logWdg.yview("end")
    logWdg.insert("end", rpt)
    
userLabel = Tkinter.Label(root, text="Type here:")
userEntry  = Tkinter.Entry(root, width=10, takefocus=1, highlightthickness=2)
logWdg = Tkinter.Text(root)

for event in eventList.values():
    userLabel.bind('<%s>' % event, reportEvent)
    userEntry.bind('<%s>' % event, reportEvent)

userLabel.grid(row=0, column=0)
userEntry.grid(row=0, column=1, sticky='ew')
logWdg.grid(row=1, column=0, columnspan=2, sticky="news")
root.rowconfigure(1, weight=1)
root.columnconfigure(1, weight=1)

userEntry.focus_set()
root.mainloop()
