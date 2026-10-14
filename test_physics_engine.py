import numpy as np
import pytest

from physics_engine import (
    harmonic_oscillator_derivative,
    integrate_rk4,
    pendulum_derivative,
    simulate_system,
)


def test_rk4_tracks_harmonic_oscillator_and_exact_end_time():
    omega = 2.0

    def derivative(_time, state):
        position, velocity = state
        return np.array([velocity, -(omega**2) * position])

    times, states = integrate_rk4(derivative, [1.0, 0.0], 1.03, 0.01)
    expected = np.cos(omega * times[-1])

    assert times[-1] == pytest.approx(1.03)
    assert states[-1, 0] == pytest.approx(expected, abs=1e-8)


def test_nonlinear_pendulum_conserves_energy_at_large_angle():
    length = 2.0
    gravity = 9.81

    def derivative(_time, state):
        angle, angular_velocity = state
        return np.array([
            angular_velocity,
            -(gravity / length) * np.sin(angle),
        ])

    _times, states = integrate_rk4(derivative, [1.2, 0.0], 20.0, 1 / 120)
    energy = (0.5 * length**2 * states[:, 1]**2
              + gravity * length * (1 - np.cos(states[:, 0])))

    assert np.ptp(energy) < 1e-6


def test_harmonic_oscillator_factory_matches_true_solution():
    times, states = simulate_system(
        harmonic_oscillator_derivative(omega=2.0),
        initial_state=[1.0, 0.0],
        duration=1.03,
        dt=0.01,
    )
    expected = np.cos(2.0 * times[-1])

    assert times[-1] == pytest.approx(1.03)
    assert states[-1, 0] == pytest.approx(expected, abs=1e-8)


def test_pendulum_factory_tracks_large_angle_energy():
    length = 2.0
    gravity = 9.81

    times, states = simulate_system(
        pendulum_derivative(length=length, gravity=gravity),
        initial_state=[1.2, 0.0],
        duration=20.0,
        dt=1 / 120,
    )
    energy = (0.5 * length**2 * states[:, 1]**2
              + gravity * length * (1 - np.cos(states[:, 0])))

    assert np.ptp(energy) < 1e-6
    assert times[-1] == pytest.approx(20.0)


@pytest.mark.parametrize(
    ("duration", "dt"),
    [(-1, 0.1), (1, 0), (float("inf"), 0.1)],
)
def test_rk4_rejects_invalid_time_steps(duration, dt):
    with pytest.raises(ValueError):
        integrate_rk4(lambda _time, state: state, [1.0], duration, dt)