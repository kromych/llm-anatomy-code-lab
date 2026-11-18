# samemodel.py A.gguf B.gguf -- do two GGUF files hold the same model?
# Prints the SHA-256 digest of each file and compares the tensors of the
# same name byte for byte (standard library only).
import hashlib, struct, sys

SCALARS = {0: "<B", 1: "<b", 2: "<H", 3: "<h", 4: "<I", 5: "<i",
           6: "<f", 7: "<?", 10: "<Q", 11: "<q", 12: "<d"}

def get(f, fmt):
    return struct.unpack(fmt, f.read(struct.calcsize(fmt)))[0]

def string(f):
    return f.read(get(f, "<Q")).decode("utf-8")

def value(f, vtype):                     # as in ggufread.py
    if vtype == 8:
        return string(f)
    if vtype == 9:
        etype, count = get(f, "<I"), get(f, "<Q")
        return [value(f, etype) for _ in range(count)]
    return get(f, SCALARS[vtype])

def read(path):
    """The digest of the file, its name for itself, and the digest of
    each tensor: the bytes from its offset to the next tensor's."""
    whole = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(1 << 24):
            whole.update(block)
        size = f.tell()
        f.seek(0)
        assert f.read(4) == b"GGUF" and get(f, "<I") == 3
        n_tensors, n_kv = get(f, "<Q"), get(f, "<Q")
        meta = {}
        for _ in range(n_kv):
            key = string(f)
            meta[key] = value(f, get(f, "<I"))
        infos = []
        for _ in range(n_tensors):
            name, ndim = string(f), get(f, "<I")
            f.read(8 * ndim + 4)         # the dimensions and the type
            infos.append((get(f, "<Q"), name))
        align = meta.get("general.alignment", 32)
        data = (f.tell() + align - 1) // align * align
        infos.sort()
        ends = [off for off, _ in infos[1:]] + [size - data]
        tensors = {}
        for (off, name), end in zip(infos, ends):
            f.seek(data + off)
            tensors[name] = hashlib.sha256(f.read(end - off)).hexdigest()
    return whole.hexdigest(), meta.get("general.name"), tensors

a, b = read(sys.argv[1]), read(sys.argv[2])
for path, (digest, name, tensors) in zip(sys.argv[1:], (a, b)):
    print(f"{digest[:16]}...  {name!r}, {len(tensors)} tensors  {path}")
common = sorted(set(a[2]) & set(b[2]))
same = [n for n in common if a[2][n] == b[2][n]]
print(f"{len(common)} tensors have the same name in both files, "
      f"{len(same)} of them the same bytes")
print("the same:", " ".join(same[:3]) or "none")
print("different:", " ".join([n for n in common if n not in same][:3])
      or "none")
