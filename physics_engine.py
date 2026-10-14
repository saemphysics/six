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