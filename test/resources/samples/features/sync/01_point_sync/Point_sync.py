import math

def _sync_from_v1_to_v2(v1_impl, v2_impl):
    v2_impl.r = math.sqrt(v1_impl.x**2 + v1_impl.y**2)
    v2_impl.theta = math.atan2(v1_impl.y, v1_impl.x)

def _sync_from_v2_to_v1(v2_impl, v1_impl):
    v1_impl.x = v2_impl.r * math.cos(v2_impl.theta)
    v1_impl.y = v2_impl.r * math.sin(v2_impl.theta)
