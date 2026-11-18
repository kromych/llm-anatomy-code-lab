import pickle, pickletools

class Innocent:
    def __reduce__(self):
        # tell pickle: "to rebuild me, call print('hello from the file')"
        return (print, ("hello from the file",))

data = pickle.dumps(Innocent(), protocol=4)
pickletools.dis(data)
pickle.loads(data)          # prints the message: loading ran code
