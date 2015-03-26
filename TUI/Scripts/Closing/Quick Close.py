def run(sr):
# quickClose.py
  from datetime import datetime
  tt=datetime.utcnow()
  yield sr.waitCmd(actor="tcc", cmdStr="track 121,30 mount")
