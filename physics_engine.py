"""Deterministic numerical tools for physics-driven animations.

The engine exposes a compact but production-friendly API for driving cinematic
simulations: a fixed-step RK4 integrator, harmonic-oscillator dynamics, and a
nonlinear pendulum model. These are intentionally generic and deterministic so
that the same state equations can be used both in numerical validation and in
rendered scenes.
"""
from __future__ import annotations

from collections.abc import Callable

import numpy as np

__all__ = [
    "integrate_rk4",
    "harmonic_oscillator_derivative",
    "pendulum_derivative",
    "simulate_system",
    "CalculusEngine",
    "GeometryEngine",
    "LinearAlgebraEngine",
    "KinematicsEngine",
    "KineticsEngine",
    "MechanicsEngine",
    "ElectrostaticsEngine",
    "MagneticsEngine",
    "FluidsEngine",
    "WavesEngine",
    "VectorCalculusEngine",
    "DifferentialEquationsEngine",
    "EngineCatalog",
]


def _validate_state_vector(initial_state: np.ndarray | list[float]) -> np.ndarray:
    """Ensure the state is a finite, non-empty 1D vector."""
    state = np.asarray(initial_state, dtype=np.float64)
    if state.ndim != 1 or state.size == 0 or not np.all(np.isfinite(state)):
        raise ValueError("initial_state must be a finite, non-empty vector")
    return state


def integrate_rk4(
    derivative: Callable[[float, np.ndarray], np.ndarray],
    initial_state: np.ndarray | list[float],
    duration: float,
    dt: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Integrate a first-order state equation with fixed-step RK4.

    The final step is shortened when needed so the returned trajectory ends
    exactly at ``duration``. State vectors and derivatives use float64.
    """
    duration = float(duration)
    dt = float(dt)
    if not np.isfinite(duration) or duration < 0:
        raise ValueError("duration must be finite and non-negative")
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be finite and positive")

    state = _validate_state_vector(initial_state)

    times = [0.0]
    states = [state.copy()]
    time = 0.0
    while time < duration:
        step = min(dt, duration - time)
        k1 = np.asarray(derivative(time, state), dtype=np.float64)
        k2 = np.asarray(derivative(time + step / 2, state + step * k1 / 2),
                        dtype=np.float64)
        k3 = np.asarray(derivative(time + step / 2, state + step * k2 / 2),
                        dtype=np.float64)
        k4 = np.asarray(derivative(time + step, state + step * k3),
                        dtype=np.float64)
        if any(k.shape != state.shape for k in (k1, k2, k3, k4)):
            raise ValueError("derivative must return a vector matching state")

        state = state + (step / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        if not np.all(np.isfinite(state)):
            raise FloatingPointError("integration produced a non-finite state")

        time += step
        times.append(time)
        states.append(state.copy())

    return np.asarray(times), np.asarray(states)


def harmonic_oscillator_derivative(
    omega: float = 1.0,
    damping: float = 0.0,
) -> Callable[[float, np.ndarray], np.ndarray]:
    """Return a harmonic oscillator derivative for [position, velocity]."""
    omega = float(omega)
    damping = float(damping)
    if not np.isfinite(omega) or omega <= 0:
        raise ValueError("omega must be a finite positive number")
    if not np.isfinite(damping):
        raise ValueError("damping must be finite")

    def derivative(_time: float, state: np.ndarray | list[float]) -> np.ndarray:
        vec = _validate_state_vector(state)
        if vec.size != 2:
            raise ValueError("harmonic oscillator state must be length 2")
        position, velocity = vec
        return np.array([
            velocity,
            -(omega ** 2) * position - damping * velocity,
        ], dtype=np.float64)

    return derivative


def pendulum_derivative(
    length: float = 1.0,
    gravity: float = 9.81,
    damping: float = 0.0,
) -> Callable[[float, np.ndarray], np.ndarray]:
    """Return a pendulum derivative for [angle, angular_velocity]."""
    length = float(length)
    gravity = float(gravity)
    damping = float(damping)
    if not np.isfinite(length) or length <= 0:
        raise ValueError("length must be a finite positive number")
    if not np.isfinite(gravity):
        raise ValueError("gravity must be finite")
    if not np.isfinite(damping):
        raise ValueError("damping must be finite")

    def derivative(_time: float, state: np.ndarray | list[float]) -> np.ndarray:
        vec = _validate_state_vector(state)
        if vec.size != 2:
            raise ValueError("pendulum state must be length 2")
        angle, angular_velocity = vec
        return np.array([
            angular_velocity,
            -(gravity / length) * np.sin(angle) - damping * angular_velocity,
        ], dtype=np.float64)

    return derivative


def simulate_system(
    derivative: Callable[[float, np.ndarray], np.ndarray],
    initial_state: np.ndarray | list[float],
    duration: float,
    dt: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Convenience wrapper around ``integrate_rk4`` for scene-driven animation."""
    return integrate_rk4(derivative, initial_state, duration, dt)


class CalculusEngine:
    """Core symbolic/numeric calculus primitives for animation math."""

    @staticmethod
    def derivative(func: Callable[[np.ndarray], np.ndarray], x: np.ndarray | float, *, h: float = 1e-6):
        x_arr = np.asarray(x, dtype=np.float64)
        if x_arr.ndim == 0:
            return float((func(x_arr + h) - func(x_arr - h)) / (2.0 * h))
        values = np.asarray(func(x_arr), dtype=np.float64)
        if values.shape != x_arr.shape:
            raise ValueError("function output must match the input shape")
        return np.gradient(values, x_arr, edge_order=2)

    @staticmethod
    def integrate(func: Callable[[np.ndarray], np.ndarray], a: float, b: float, n: int = 1000) -> float:
        if n < 2:
            raise ValueError("n must be at least 2")
        xs = np.linspace(float(a), float(b), int(n) + 1)
        ys = np.asarray(func(xs), dtype=np.float64)
        return float(np.trapezoid(ys, xs))


class GeometryEngine:
    """Euclidean geometry primitives used in visual proofs and diagrams."""

    @staticmethod
    def distance(point_a, point_b) -> float:
        a = np.asarray(point_a, dtype=np.float64)
        b = np.asarray(point_b, dtype=np.float64)
        return float(np.linalg.norm(a - b))

    @staticmethod
    def angle_between(vector_a, vector_b) -> float:
        a = np.asarray(vector_a, dtype=np.float64)
        b = np.asarray(vector_b, dtype=np.float64)
        denominator = np.linalg.norm(a) * np.linalg.norm(b)
        if denominator == 0.0:
            raise ValueError("angle between zero vectors is undefined")
        cosine = np.clip(np.dot(a, b) / denominator, -1.0, 1.0)
        return float(np.arccos(cosine))

    @staticmethod
    def line_equation(point_a, point_b):
        a = np.asarray(point_a, dtype=np.float64)
        b = np.asarray(point_b, dtype=np.float64)
        delta = b - a
        if np.allclose(delta, 0.0):
            raise ValueError("line endpoints must be distinct")
        slope = delta[1] / delta[0] if abs(delta[0]) > 1e-12 else np.inf
        intercept = a[1] - slope * a[0]
        return slope, intercept


class LinearAlgebraEngine:
    """Lightweight linear algebra utilities for vector and matrix problems."""

    @staticmethod
    def dot(vector_a, vector_b):
        a = np.asarray(vector_a, dtype=np.float64)
        b = np.asarray(vector_b, dtype=np.float64)
        return float(np.dot(a, b))

    @staticmethod
    def matrix_vector_product(matrix, vector):
        m = np.asarray(matrix, dtype=np.float64)
        v = np.asarray(vector, dtype=np.float64)
        return np.asarray(m @ v, dtype=np.float64)

    @staticmethod
    def normalize(vector):
        v = np.asarray(vector, dtype=np.float64)
        norm = np.linalg.norm(v)
        if norm == 0.0:
            raise ValueError("cannot normalize a zero vector")
        return v / norm


class KinematicsEngine:
    """1D/2D kinematics for cinematic motion studies."""

    @staticmethod
    def constant_acceleration_position(x0: float, v0: float, a: float, t: float) -> float:
        return float(x0 + v0 * t + 0.5 * a * t ** 2)

    @staticmethod
    def constant_acceleration_velocity(v0: float, a: float, t: float) -> float:
        return float(v0 + a * t)


KineticsEngine = KinematicsEngine


class MechanicsEngine:
    """Classical mechanics models for trajectories and oscillations."""

    @staticmethod
    def projectile_trajectory(speed: float, angle_deg: float, dt: float, gravity: float = 9.81, max_time: float = 10.0):
        theta = np.deg2rad(float(angle_deg))
        vx = float(speed) * np.cos(theta)
        vy = float(speed) * np.sin(theta)
        x = 0.0
        y = 0.0
        positions = [(x, y)]
        t = 0.0
        while y >= 0.0 and t <= max_time:
            x = vx * t
            y = vy * t - 0.5 * gravity * t ** 2
            positions.append((x, y))
            t += float(dt)
        return positions

    @staticmethod
    def spring_force(k: float, x: float) -> float:
        return float(-k * x)


class ElectrostaticsEngine:
    """Coulomb-law electric field computations for charge diagrams."""

    @staticmethod
    def electric_field(positions, charges, point, k: float = 8.9875517923e9):
        p = np.asarray(point, dtype=np.float64)
        pos = np.asarray(positions, dtype=np.float64)
        q = np.asarray(charges, dtype=np.float64)
        if pos.shape[-1] != 3 or p.shape != (3,):
            raise ValueError("positions and point must be 3D vectors")
        if pos.shape[0] != q.shape[0]:
            raise ValueError("charges and positions must have matching lengths")

        field = np.zeros(3, dtype=np.float64)
        for charge_position, charge in zip(pos, q):
            delta = p - charge_position
            radius_sq = np.dot(delta, delta)
            if radius_sq < 1e-12:
                continue
            field += k * charge * delta / (radius_sq ** 1.5)
        return field


class MagneticsEngine:
    """Simple magnetostatics approximations for wire and loop visualizations."""

    @staticmethod
    def magnetic_field(wire_point, current: float, observation, mu0: float = 4e-7 * np.pi):
        p = np.asarray(wire_point, dtype=np.float64)
        o = np.asarray(observation, dtype=np.float64)
        if p.shape != (3,) or o.shape != (3,):
            raise ValueError("wire_point and observation must be 3D vectors")
        delta = o - p
        radius_sq = np.dot(delta, delta)
        if radius_sq < 1e-12:
            radius_sq = 1e-12
        direction = np.array([0.0, 0.0, 1.0])
        field = mu0 * float(current) * np.cross(direction, delta) / (2.0 * np.pi * radius_sq)
        return field


class FluidsEngine:
    """Fluid-flow field primitives for streamlines and visualized velocity fields."""

    @staticmethod
    def velocity_field(x, y, t=0.0):
        x_val = float(x)
        y_val = float(y)
        return np.array([
            np.sin(x_val + t),
            np.cos(y_val - t),
        ], dtype=np.float64)

    @staticmethod
    def continuity_error(field):
        field_array = np.asarray(field, dtype=np.float64)
        return float(np.linalg.norm(field_array))


class WavesEngine:
    """Wave equations for traveling, standing, and interference patterns."""

    @staticmethod
    def traveling_wave(amplitude: float, wave_number: float, angular_frequency: float, phase: float, x: float, t: float) -> float:
        return float(amplitude * np.sin(wave_number * x - angular_frequency * t + phase))

    @staticmethod
    def standing_wave(amplitude: float, wave_number: float, angular_frequency: float, phase: float, x: float, t: float) -> float:
        return float(2.0 * amplitude * np.sin(wave_number * x + phase) * np.cos(angular_frequency * t))


class VectorCalculusEngine:
    """Advanced vector calculus for beautiful visual intuition in multivariable settings."""

    @staticmethod
    def gradient(scalar_field, point):
        p = np.asarray(point, dtype=np.float64)
        if p.size == 2:
            x, y = p
            fx = scalar_field(np.array([x, y]))
            h = 1e-6
            gx = (scalar_field(np.array([x + h, y])) - fx) / h
            gy = (scalar_field(np.array([x, y + h])) - fx) / h
            return np.array([gx, gy], dtype=np.float64)
        if p.size == 3:
            x, y, z = p
            h = 1e-6
            f0 = scalar_field(np.array([x, y, z]))
            dx = (scalar_field(np.array([x + h, y, z])) - f0) / h
            dy = (scalar_field(np.array([x, y + h, z])) - f0) / h
            dz = (scalar_field(np.array([x, y, z + h])) - f0) / h
            return np.array([dx, dy, dz], dtype=np.float64)
        raise ValueError("point must be 2D or 3D")

    @staticmethod
    def divergence(vector_field, point):
        p = np.asarray(point, dtype=np.float64)
        h = 1e-6
        if p.size == 2:
            vx = vector_field(p)[0]
            vy = vector_field(p)[1]
            d1 = (vector_field(p + np.array([h, 0.0]))[0] - vx) / h
            d2 = (vector_field(p + np.array([0.0, h]))[1] - vy) / h
            return float(d1 + d2)
        raise ValueError("divergence implemented for 2D fields only")


class DifferentialEquationsEngine:
    """Core differential equation models for intuitive dynamic explanation."""

    @staticmethod
    def exponential_decay(k: float = 1.0, t: float = 0.0, initial_value: float = 1.0) -> float:
        return float(initial_value * np.exp(-float(k) * float(t)))

    @staticmethod
    def harmonic_response(omega: float = 1.0, t: float = 0.0, amplitude: float = 1.0) -> float:
        return float(amplitude * np.sin(float(omega) * float(t)))


# Backwards-compatible alias for the original motion-engine naming.
Mechanics = MechanicsEngine
Electrostatics = ElectrostaticsEngine
Magnetics = MagneticsEngine
Fluids = FluidsEngine
Waves = WavesEngine
Kinematics = KinematicsEngine


class EngineCatalog:
    """Registry and resolution utilities for the domain engine library."""

    _registry = {
        "calculus": CalculusEngine,
        "geometry": GeometryEngine,
        "linear_algebra": LinearAlgebraEngine,
        "kinematics": KinematicsEngine,
        "mechanics": MechanicsEngine,
        "electrostatics": ElectrostaticsEngine,
        "magnetics": MagneticsEngine,
        "fluids": FluidsEngine,
        "waves": WavesEngine,
        "vector_calculus": VectorCalculusEngine,
        "differential_equations": DifferentialEquationsEngine,
    }

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._registry)

    @classmethod
    def resolve(cls, name: str):
        key = str(name).strip().lower().replace(" ", "_").replace("-", "_")
        alias_map = {
            "linearalgebra": "linear_algebra",
            "lin_alg": "linear_algebra",
            "electrodynamics": "electrostatics",
        }
        key = alias_map.get(key, key)
        if key not in cls._registry:
            raise KeyError(f"unsupported engine: {name!r}")
        return cls._registry[key]

    @classmethod
    def instantiate(cls, name: str, **kwargs):
        engine = cls.resolve(name)
        if isinstance(engine, type):
            return engine(**kwargs)
        return engine

    @classmethod
    def describe(cls) -> dict[str, str]:
        descriptions = {
            "calculus": "Derivatives, integrals, and analytic approximation tools.",
            "geometry": "Distance, angle, and Euclidean object primitives.",
            "linear_algebra": "Vector, matrix, and basis operations for visual proofs.",
            "kinematics": "Position and velocity evolution under simple motion models.",
            "mechanics": "Projectile, harmonic, and force-driven dynamical systems.",
            "electrostatics": "Coulomb field generation and charge interactions.",
            "magnetics": "Magnetic field approximations and current-centric geometry.",
            "fluids": "Velocity-field and streamline-like flow primitives.",
            "waves": "Traveling and standing waves for interference visuals.",
            "vector_calculus": "Gradient, divergence, and flow intuition in multiple dimensions.",
            "differential_equations": "Decay, resonance, and dynamic evolution at the heart of physics.",
        }
        return {key: descriptions.get(key, "") for key in cls.available()}
