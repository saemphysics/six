import numpy as np
import pytest

from narrative_engine import NarrativeEngine
from physics_engine import (
    CalculusEngine,
    ElectrostaticsEngine,
    EngineCatalog,
    FluidsEngine,
    GeometryEngine,
    KinematicsEngine,
    LinearAlgebraEngine,
    MagneticsEngine,
    MechanicsEngine,
    WavesEngine,
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


def test_calculus_engine_derivative_and_integral_are_consistent():
    values = np.linspace(0.0, 2.0, 101)
    derivative = CalculusEngine.derivative(np.sin, values)
    integral = CalculusEngine.integrate(np.sin, 0.0, 2.0, 1000)

    assert np.all(np.isfinite(derivative))
    assert integral == pytest.approx(1.0 - np.cos(2.0), rel=1e-3)


def test_geometry_and_linear_algebra_engines_work_on_vectors():
    a = np.array([0.0, 0.0])
    b = np.array([3.0, 4.0])
    assert GeometryEngine.distance(a, b) == pytest.approx(5.0)
    assert LinearAlgebraEngine.dot(np.array([1.0, 2.0]), np.array([3.0, 4.0])) == pytest.approx(11.0)
    assert LinearAlgebraEngine.matrix_vector_product(
        np.array([[1.0, 2.0], [0.0, 1.0]]),
        np.array([3.0, 4.0]),
    ).tolist() == pytest.approx([11.0, 4.0])


def test_mechanics_and_kinematics_engines_model_motion():
    x0, v0 = 0.0, 10.0
    x_t = KinematicsEngine.constant_acceleration_position(x0, v0, 0.0, 2.0)
    assert x_t == pytest.approx(20.0)

    trajectory = MechanicsEngine.projectile_trajectory(10.0, 45.0, 0.1)
    assert len(trajectory) > 0
    assert trajectory[0][1] == pytest.approx(0.0)
    assert trajectory[-1][1] <= 0.0


def test_electrostatics_magnetics_waves_and_fluids_engines_produce_fields():
    E = ElectrostaticsEngine.electric_field(
        positions=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
        charges=np.array([1.0, -1.0]),
        point=np.array([0.5, 0.0, 0.0]),
    )
    assert E.shape == (3,)
    assert np.all(np.isfinite(E))

    B = MagneticsEngine.magnetic_field(
        wire_point=np.array([0.0, 0.0, 0.0]),
        current=1.0,
        observation=np.array([0.0, 1.0, 0.0]),
    )
    assert B.shape == (3,)
    assert np.all(np.isfinite(B))

    wave = WavesEngine.traveling_wave(amplitude=1.0, wave_number=2.0, angular_frequency=3.0, phase=0.0, x=0.5, t=0.25)
    assert wave == pytest.approx(np.sin(2.0 * 0.5 - 3.0 * 0.25))

    flow = FluidsEngine.velocity_field(x=1.0, y=2.0, t=0.5)
    assert flow.shape == (2,)
    assert np.all(np.isfinite(flow))


def test_domain_registry_exposes_every_engine_and_resolves_class_names():
    names = EngineCatalog.available()
    required = {
        "calculus", "geometry", "linear_algebra", "kinematics", "mechanics",
        "electrostatics", "magnetics", "fluids", "waves",
    }
    assert required.issubset(set(names))
    assert EngineCatalog.resolve("mechanics") is MechanicsEngine
    assert EngineCatalog.resolve("waves") is WavesEngine
    assert EngineCatalog.resolve("calculus") is CalculusEngine


def test_narrative_engine_builds_a_coherent_story_arc():
    beats = NarrativeEngine.build_story("pendulum", ["mechanics", "calculus", "waves"])
    assert len(beats) >= 4
    assert beats[0].title == "setup"
    assert all(beat.engine in {"mechanics", "calculus", "waves"} for beat in beats)
    assert all(beat.goal for beat in beats)


def test_narrative_plan_generates_topic_blueprint_and_voiceover():
    plan = NarrativeEngine.topic_blueprint("wave interference", ["waves", "mechanics"])
    assert plan["topic"] == "wave interference"
    assert plan["domains"] == ["waves", "mechanics"]
    assert plan["motif"]
    assert len(plan["voiceover"]) >= 3
    assert plan["scene_plan"][0]["title"] == "setup"