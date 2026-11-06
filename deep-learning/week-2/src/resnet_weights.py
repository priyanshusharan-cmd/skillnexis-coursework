"""Loads the original Keras ResNet50 ImageNet weights file (old layer names: res2a_branch2a, bn2a_branch2a ...) into
today's keras.applications.ResNet50 (conv2_block1_1_conv, conv2_block1_1_bn ...) by translating the names, because
the two graphs list their layers in different orders. Every layer is matched; anything left over raises an error."""
import h5py, numpy as np
def _new_name(old):
    if old == "conv1": return "conv1_conv"
    if old == "bn_conv1": return "conv1_bn"
    import re
    m = re.match(r"(res|bn)(\d)([a-z])_branch(2a|2b|2c|1)$", old)
    if not m: return None
    kind, stage, blk, br = m.groups(); n = ord(blk) - 96; part = {"2a": 1, "2b": 2, "2c": 3, "1": 0}[br]
    return f"conv{stage}_block{n}_{part}_" + ("conv" if kind == "res" else "bn")
def load(model, path):
    f = h5py.File(path, "r"); names = [n.decode() if isinstance(n, bytes) else n for n in f.attrs["layer_names"]]; done = set()
    for old in names:
        new = _new_name(old); g = f[old]; ws = [np.array(g[w]) for w in g.attrs["weight_names"]]
        if new is None:
            assert not ws, f"unmapped layer with weights: {old}"; continue
        layer = model.get_layer(new); exp = [w.shape for w in layer.get_weights()]
        assert [w.shape for w in ws] == exp, (old, new, [w.shape for w in ws], exp); layer.set_weights(ws); done.add(new)
    missing = [l.name for l in model.layers if l.get_weights() and l.name not in done]
    assert not missing, f"layers without weights: {missing}"; return len(done)
