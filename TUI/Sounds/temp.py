import Tkinter
import tkSnack
filename = "MessageReceived.wav" # set to the path to a sound file somewhere

root = Tkinter.Tk()
tkSnack.initializeSnack(root)
snd = tkSnack.Sound(load = filename)
Tkinter.Button(root, text="Play", command=snd.play).pack()
root.mainloop()