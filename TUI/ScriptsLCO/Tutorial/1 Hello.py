class ScriptClass(object):
    def __init__(self, sr):
        pass

    def run(self, sr):
        sr.showMsg("Hello")
        yield sr.waitMS(1000)
