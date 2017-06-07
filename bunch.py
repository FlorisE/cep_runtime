class Bunch(dict):
    def __getattr__(self, attr):
        print self[attr]
