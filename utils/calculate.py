# 计算恒定度
# 恒定度 = (最大值 - 最小值) * 100 / (最大值 + 最小值)
def calculate_constancy(points):
    maxP = max(points)
    minP = min(points)
    return (maxP - minP) * 100 / (maxP + minP)

# 计算平均载荷偏差度
# 平均载荷偏差度 λ = |Wg - Wp| / Wg * 100%
# Wg: 工作载荷（设计载荷），Wp: (最大载荷 + 最小载荷)/2
def calculate_load_deviation(Wg, points):
    if not points:
        return 0.0
    W_max = max(points)
    W_min = min(points)
    Wp = (W_max + W_min) / 2
    deviation = abs(Wg - Wp) / Wg * 100
    return deviation
    