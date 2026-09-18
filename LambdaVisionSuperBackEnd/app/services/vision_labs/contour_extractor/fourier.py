from __future__ import annotations

import numpy as np


def _closed_arc_resample(points: np.ndarray, count: int = 128) -> np.ndarray:
    pts = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    count = max(16, int(count))
    if len(pts) < 2:
        return np.repeat(pts[:1] if len(pts) else np.zeros((1, 2)), count, axis=0)
    closed = np.vstack([pts, pts[:1]])
    seg = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    total = float(seg.sum())
    if total <= 1e-12:
        return np.repeat(pts[:1], count, axis=0)
    cumulative = np.concatenate([[0.0], np.cumsum(seg)])
    targets = np.linspace(0.0, total, count, endpoint=False)
    result = np.empty((count, 2), dtype=np.float64)
    for i, target in enumerate(targets):
        idx = min(len(seg) - 1, max(0, int(np.searchsorted(cumulative, target, side="right") - 1)))
        local = (target - cumulative[idx]) / max(seg[idx], 1e-12)
        result[i] = closed[idx] * (1.0 - local) + closed[idx + 1] * local
    return result


def contour_fourier_descriptor(points: np.ndarray, *, harmonics: int = 16, sample_count: int = 128) -> np.ndarray:
    """Translation/scale/rotation-invariant magnitude Fourier descriptor.

    The contour is uniformly resampled by arc length, centered, normalized by
    RMS radius, encoded as z=x+i*y and transformed with FFT. Taking coefficient
    magnitudes removes global rotation/starting-phase sensitivity sufficiently
    for an interactive shape-finding primitive.
    """

    sampled = _closed_arc_resample(points, sample_count)
    sampled = sampled - sampled.mean(axis=0, keepdims=True)
    scale = float(np.sqrt(np.mean(np.sum(sampled * sampled, axis=1))))
    if scale <= 1e-12:
        scale = 1.0
    sampled /= scale
    signal = sampled[:, 0] + 1j * sampled[:, 1]
    coeff = np.fft.fft(signal) / len(signal)
    count = max(1, min(int(harmonics), len(coeff) // 2 - 1))
    # Ignore DC. Pair positive/negative magnitudes into one descriptor element.
    values = []
    for k in range(1, count + 1):
        values.append(float(np.sqrt(abs(coeff[k]) ** 2 + abs(coeff[-k]) ** 2)))
    arr = np.asarray(values, dtype=np.float64)
    norm = float(np.linalg.norm(arr))
    if norm > 1e-12:
        arr /= norm
    return arr.astype(np.float32)


def contour_fourier_reconstruction(points: np.ndarray, *, harmonics: int = 8, sample_count: int = 128) -> np.ndarray:
    """Reconstruct a contour with only the lowest N harmonic pairs.

    Returned coordinates are transformed back into the original contour's
    centroid/RMS scale, which makes original-vs-reconstruction visualization
    intuitive for users learning Fourier shape descriptors.
    """

    original = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    sampled = _closed_arc_resample(original, sample_count)
    center = sampled.mean(axis=0, keepdims=True)
    centered = sampled - center
    scale = float(np.sqrt(np.mean(np.sum(centered * centered, axis=1))))
    if scale <= 1e-12:
        scale = 1.0
    normalized = centered / scale
    signal = normalized[:, 0] + 1j * normalized[:, 1]
    coeff = np.fft.fft(signal)
    keep = max(1, min(int(harmonics), len(coeff) // 2 - 1))
    masked = np.zeros_like(coeff)
    masked[0] = coeff[0]
    for k in range(1, keep + 1):
        masked[k] = coeff[k]
        masked[-k] = coeff[-k]
    reconstructed = np.fft.ifft(masked)
    points_out = np.column_stack([reconstructed.real, reconstructed.imag]) * scale + center
    return points_out.astype(np.float32)
