from yirgacheffe.layers import Layer
import sys

l = Layer.layer_from_file(sys.argv[1])
d = {}

def f(x):
    try:
        d[x] = d[x] + 1
    except KeyError:
        d[x] = 1
    return 0.0

l.shader_apply(f).sum()
print(d)