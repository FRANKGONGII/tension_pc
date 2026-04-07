import statistics

# 目标恒定度（相对比值，非百分数）；用于由 M、m 反推缩放系数 α
TARGET_CONSTANCY_FRACTION = 0.05


def robust_min_max_means(points):
    """
    与恒定度一致：排序后取最小 k、最大 k 个点的算术平均，k = min(5, n)。
    返回 (m, M)，m 为低端均值，M 为高端均值；points 为空时返回 (None, None)。
    """
    if not points:
        return None, None
    sorted_pts = sorted(points)
    n = len(points)
    k = min(5, n)
    M = sum(sorted_pts[-k:]) / k
    m = sum(sorted_pts[:k]) / k
    return m, M


# 计算恒定度
# 恒定度 = (最大值 - 最小值) * 100 / (最大值 + 最小值)，其中最大/最小为 robust_min_max_means
def calculate_constancy(points):
    m, M = robust_min_max_means(points)
    if m is None or M + m == 0:
        return 0.0
    return (M - m) * 100 / (M + m)


def scale_alpha_for_target_constancy(M, m, target_fraction=TARGET_CONSTANCY_FRACTION):
    """
    使 M' = M(1-α)、m' = m(1+α) 满足 (M'-m')/(M'+m') = target_fraction（如 0.05 即 5%）。
    α = (A - t*B) / (B - t*A)，A=M-m, B=M+m。
    """
    if M <= 0 or m <= 0:
        return 0.0
    t = max(1e-6, min(float(target_fraction), 0.999))
    A = M - m
    B = M + m
    denom = B - t * A
    if abs(denom) < 1e-15:
        return 0.0
    alpha = (A - t * B) / denom
    # 保证 M(1-α)、m(1+α) 为正，并限制幅度避免数值失控
    alpha = max(alpha, -0.99)
    alpha = min(alpha, 0.99)
    if M * (1.0 - alpha) <= 0 or m * (1.0 + alpha) <= 0:
        return 0.0
    return alpha


def apply_branch_scale_sequence(xs, ys, alpha, delta):
    """
    与在线逻辑一致：位移峰值滞回 + 单向卸载相。
    加载相 x*(1-α)；当 y <= y_running_max - δ 后锁定为卸载相，x*(1+α)。
    xs、ys 等长；alpha 通常 ∈ [0, 0.99]。
    """
    if not xs or len(xs) != len(ys):
        return list(xs) if xs else []
    out = []
    y_running_max = None
    phase_descending = False
    a = float(alpha)
    d = float(delta)
    for x, y in zip(xs, ys):
        if not phase_descending:
            if y_running_max is None:
                y_running_max = y
            else:
                y_running_max = max(y_running_max, y)
            if y_running_max is not None and y <= y_running_max - d:
                phase_descending = True
        if not phase_descending:
            out.append(x * (1.0 - a))
        else:
            out.append(x * (1.0 + a))
    return out


def median_filter_like_widget(sequence, window_n=5):
    """与 test_widget_1 中力值中值滤波一致（首点填满窗口后输出原值，之后滑窗中位数）。"""
    if not sequence:
        return []
    out = []
    buf = None
    n = int(window_n)
    if n < 1:
        n = 1
    for x in sequence:
        if buf is None:
            buf = [x] * n
            out.append(x)
        else:
            buf.append(x)
            if len(buf) > n:
                buf.pop(0)
            out.append(statistics.median(buf))
    return out


def median_filter_hysteresis_by_y_peak(ys, values, window_n=5):
    """
    在位移 y 首次达到全程最大值的下标处拆成两段（上升臂 / 下降臂），
    各段内分别做时间序中值滤波后再拼接，避免两支力值在同一滑窗内混叠导致 x 交叉。
    峰值在首点或末点时退化为整段滤波。
    """
    n = len(values)
    if n == 0 or len(ys) != n:
        return median_filter_like_widget(values, window_n)
    y_max = max(ys)
    peak_i = min(i for i in range(n) if ys[i] == y_max)
    if peak_i == 0 or peak_i == n - 1:
        return median_filter_like_widget(values, window_n)
    seg1 = values[: peak_i + 1]
    seg2 = values[peak_i:]
    f1 = median_filter_like_widget(seg1, window_n)
    f2 = median_filter_like_widget(seg2, window_n)
    merged = f1[:-1] + [0.5 * (f1[-1] + f2[0])] + f2[1:]
    if len(merged) != n:
        return median_filter_like_widget(values, window_n)
    return merged


def apply_symmetric_extreme_pull(xs, phi, m_ref, M_ref, gamma=2.0):
    """
    两臂对称向中心 c=(m+M)/2 压缩：x' = c + (x-c)·(1 - φ·e)，
    e = |2u-1|^γ，u 为 x 在 [m_ref,M_ref] 上的归一化位置；u=0.5 时 e=0 不变，越靠近两端 e 越大、压缩越强。
    k=1-φ·e 下限 0.25，避免一次拉穿；沿 x 单调性在 φ 适中时通常保持，利于避免两支交叉。
    """
    if not xs or m_ref is None or M_ref is None:
        return list(xs) if xs else []
    m_ref = float(m_ref)
    M_ref = float(M_ref)
    span = M_ref - m_ref
    if span <= 1e-15:
        return [float(x) for x in xs]
    c = 0.5 * (m_ref + M_ref)
    phi = float(phi)
    gamma = float(gamma)
    out = []
    for x in xs:
        xf = float(x)
        u = (xf - m_ref) / span
        u = max(0.0, min(1.0, u))
        e = abs(2.0 * u - 1.0) ** gamma
        k = 1.0 - phi * e
        if k < 0.25:
            k = 0.25
        elif k > 1.0:
            k = 1.0
        out.append(c + (xf - c) * k)
    return out


def constancy_after_branch_scale_and_filter(prescale_xs, ys, alpha, delta, window_n=5):
    """对预缩放力值序列做分支缩放 + 中值滤波后的恒定度（百分数，与 calculate_constancy 一致）。"""
    scaled = apply_branch_scale_sequence(prescale_xs, ys, alpha, delta)
    filtered = median_filter_like_widget(scaled, window_n)
    return calculate_constancy(filtered)


def apply_proportional_constancy_pull(xs, phi, m_ref, M_ref, min_hold=True):
    """
    按与稳健极值的距离加权，将力值向中心 c=(m_ref+M_ref)/2 拉拢：越接近高端 M 的改动越大，
    越接近中线改动越小（e→0）。
    min_hold=True（默认）：仅对 x>c 的点收缩，x<=c 不变，满足「低端尽量不动」。
    min_hold=False：对全程用 e=(2u-1)^2，两端（近 m、近 M）改动大、中线附近改动小。
    m_ref、M_ref 通常取本段数据的 robust_min_max_means，且在迭代中保持固定。
    """
    if not xs or m_ref is None or M_ref is None:
        return list(xs) if xs else []
    span = float(M_ref) - float(m_ref)
    if span <= 1e-15:
        return [float(x) for x in xs]
    c = 0.5 * (float(m_ref) + float(M_ref))
    phi = float(phi)
    Mc = float(M_ref) - c
    out = []
    if min_hold:
        if Mc <= 1e-15:
            return [float(x) for x in xs]
        for x in xs:
            x = float(x)
            if x <= c:
                out.append(x)
            else:
                t = (x - c) / Mc
                t = max(0.0, min(1.0, t))
                e = t * t
                xp = x - phi * e * (x - c)
                out.append(max(xp, 1e-9))
    else:
        for x in xs:
            x = float(x)
            u = (x - float(m_ref)) / span
            u = max(0.0, min(1.0, u))
            e = (2.0 * u - 1.0) ** 2
            xp = x - phi * e * (x - c)
            out.append(max(xp, 1e-9))
    return out


def constancy_after_proportional_pull_and_filter(xs, phi, m_ref, M_ref, window_n=5, min_hold=True):
    pulled = apply_proportional_constancy_pull(xs, phi, m_ref, M_ref, min_hold=min_hold)
    filtered = median_filter_like_widget(pulled, window_n)
    return calculate_constancy(filtered)


def bisect_phi_proportional_constancy_cap(
    xs, target_percent, window_n=5, min_hold=True, max_iter=48, phi_max=None
):
    """
    在 [0, phi_max] 上二分求最小 φ，使「按比例拉拢 + 中值滤波」后的恒定度 <= target_percent。
    权重基于原始序列的稳健 m、M（固定，不随 φ 重算）。
    min_hold 时默认 phi_max=1.0，避免高端被拉穿到 c 以下导致数值发散；对称模式默认 phi_max=2.0。
    若 φ=0 已合格则返回 0；若 φ=phi_max 仍不合格则返回 phi_max。
    """
    if not xs:
        return 0.0
    m_ref, M_ref = robust_min_max_means(xs)
    if m_ref is None or M_ref is None:
        return 0.0
    if phi_max is None:
        phi_max = 1.0 if min_hold else 2.0
    phi_max = float(phi_max)
    tp = float(target_percent)

    def eval_c(phi):
        return constancy_after_proportional_pull_and_filter(
            xs, phi, m_ref, M_ref, window_n, min_hold=min_hold
        )

    if eval_c(0.0) <= tp:
        return 0.0
    if eval_c(phi_max) > tp:
        return phi_max

    left, right = 0.0, phi_max
    for _ in range(max_iter):
        if right - left < 1e-6:
            break
        mid = 0.5 * (left + right)
        if eval_c(mid) <= tp:
            right = mid
        else:
            left = mid
    return right


def solve_constancy_pull_params(xs, ys, target_percent, window_n=5, gamma=2.0):
    """
    由参考曲线的力值 x、位移 y 与目标恒定度（百分数）一次性解出固定参数：
    m_ref、M_ref、φ、gamma。拉拢为对称「两臂向中心、极值处更强」；滤波优先用按 y 峰值分段中值。
    ys 与 xs 等长时启用滞回分段滤波；否则退化为整段中值。
    """
    if not xs:
        return None
    m0, M0 = robust_min_max_means(xs)
    if m0 is None or M0 is None:
        return None
    tp = float(target_percent)
    use_hyst = ys is not None and len(ys) == len(xs)
    gamma = float(gamma)

    def eval_c(phi):
        pulled = apply_symmetric_extreme_pull(xs, phi, m0, M0, gamma)
        if use_hyst:
            filt = median_filter_hysteresis_by_y_peak(ys, pulled, window_n)
        else:
            filt = median_filter_like_widget(pulled, window_n)
        return calculate_constancy(filt)

    if eval_c(0.0) <= tp:
        return {
            "m_ref": float(m0),
            "M_ref": float(M0),
            "phi": 0.0,
            "gamma": gamma,
        }
    phi_max = 1.35
    if eval_c(phi_max) > tp:
        phi_use = phi_max
    else:
        lo, hi = 0.0, phi_max
        for _ in range(56):
            if hi - lo < 1e-6:
                break
            mid = 0.5 * (lo + hi)
            if eval_c(mid) <= tp:
                hi = mid
            else:
                lo = mid
        phi_use = hi
    return {
        "m_ref": float(m0),
        "M_ref": float(M0),
        "phi": float(phi_use),
        "gamma": gamma,
    }


def fit_proportional_constancy_median(xs, target_percent, window_n=5, ys=None, gamma=2.0):
    """
    对单段序列做「解参 + 对称拉拢 + 滤波」（预览/入库用）。
    返回 (滤波后序列, φ, gamma, m_ref, M_ref)；无数据时 ([], 0, 2.0, None, None)。
    """
    p = solve_constancy_pull_params(xs, ys, target_percent, window_n, gamma)
    if p is None:
        return [], 0.0, float(gamma), None, None
    pulled = apply_symmetric_extreme_pull(
        xs, p["phi"], p["m_ref"], p["M_ref"], p["gamma"]
    )
    if ys is not None and len(ys) == len(xs):
        out = median_filter_hysteresis_by_y_peak(ys, pulled, window_n)
    else:
        out = median_filter_like_widget(pulled, window_n)
    return out, p["phi"], p["gamma"], p["m_ref"], p["M_ref"]


def bisect_alpha_constancy_cap(prescale_xs, ys, target_percent, delta, window_n=5, max_iter=48):
    """
    在 [0, 0.99] 内二分求最小 α，使滤波后恒定度 <= target_percent（百分数）。
    若 α=0.99 仍高于目标，返回 0.99（尽力而为）。
    prescale_xs、ys 须等长且非空。
    """
    if not prescale_xs or len(prescale_xs) != len(ys):
        return 0.0
    tp = float(target_percent)

    def eval_c(alpha):
        return constancy_after_branch_scale_and_filter(
            prescale_xs, ys, alpha, delta, window_n
        )

    if eval_c(0.0) <= tp:
        return 0.0
    if eval_c(0.99) > tp:
        return 0.99

    left, right = 0.0, 0.99
    for _ in range(max_iter):
        if right - left < 1e-7:
            break
        mid = 0.5 * (left + right)
        if eval_c(mid) <= tp:
            right = mid
        else:
            left = mid
    return right


# 计算锁定位置
# 锁定位置 = 实测位移值 / 去0时记录的y位置到最大y值的距离
def calculate_lock_position(measured_displacement, y_max):
    """锁定位置 = 实测位移值 / 去0时记录的y位置到最大y值的距离"""
    if y_max is None or y_max == 0:
        return None
    return measured_displacement / y_max

# 计算平均载荷偏差度
# 平均载荷偏差度 λ = |Wg - Wp| / Wg * 100%
# Wg: 工作载荷（设计载荷），Wp: (最大载荷 + 最小载荷)/2
def calculate_load_deviation(Wg, points):
    if not points:
        return 0.0
    Wp = sum(points[:5]) / min(5, len(points))
    deviation = abs(Wg - Wp) / Wg * 100
    return deviation
    