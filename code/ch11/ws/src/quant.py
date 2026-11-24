def quantize(block):
    d = max(abs(x) for x in block) / 127 or 1.0
    return d, [round(x / d) for x in block]

def dequantize(d, q):
    return [d * v for v in q]
