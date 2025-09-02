import math

def _sync_from_v1_to_v2(v1_impl, v2_impl):
    v2_impl.value = v1_impl.value

def _sync_from_v2_to_v1(v2_impl, v1_impl):
    v1_impl.value = v2_impl.value
