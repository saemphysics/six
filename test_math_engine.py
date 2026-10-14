import numpy as np
import pytest

from math_engine import (
    AdvancedCalculusEngine,
    CalculusEngine,
    GeometryEngine,
    LinearAlgebraEngine,
    VectorCalculusEngine,
)
from physics_engine import CalculusEngine as PhysicsCalculusEngine
from physics_engine import EngineCatalog


def test_mathematics_engines_are_separate_and_keep_compatibility_exports():
    assert PhysicsCalculusEngine is CalculusEngine
    assert EngineCatalog.resolve("calculus") is CalculusEngine
    assert EngineCatalog.resolve("vector_calculus") is VectorCalculusEngine


def test_calculus_validates_samples_and_supports_scalar_derivatives():
    assert CalculusEngine.derivative(lambda x: x**2, 3.0) == pytest.approx(6.0)
    assert CalculusEngine.integrate(lambda x: x**2, 0.0, 1.0, n=1000) == pytest.approx(
        1 / 3,
        abs=1e-6,
    )
    with pytest.raises(ValueError, match="strictly increasing"):
        CalculusEngine.derivative(np.sin, np.array([0.0, 1.0, 0.5]))


def test_vector_calculus_handles_three_dimensional_fields():
    point = np.array([1.0, 2.0, 3.0])
    gradient = VectorCalculusEngine.gradient(
        lambda p: p[0] ** 2 + 2 * p[1] ** 2 + 3 * p[2] ** 2,
        point,
    )
    divergence = VectorCalculusEngine.divergence(
        lambda p: np.array([p[0], 2 * p[1], 3 * p[2]]),
        point,
    )
    curl = VectorCalculusEngine.curl(
        lambda p: np.array([-p[1], p[0], 0.0]),
        point,
    )

    assert gradient == pytest.approx([2.0, 8.0, 18.0])
    assert divergence == pytest.approx(6.0)
    assert curl == pytest.approx([0.0, 0.0, 2.0])


def test_math_geometry_and_linear_algebra_reject_incompatible_dimensions():
    with pytest.raises(ValueError, match="matching shapes"):
        GeometryEngine.distance([0.0, 0.0], [1.0])
    with pytest.raises(ValueError, match="dimensions are incompatible"):
        LinearAlgebraEngine.matrix_vector_product([[1.0, 2.0]], [1.0])


def test_advanced_calculus_jacobian_hessian_and_curve_samples():
    point = np.array([2.0, 3.0])
    jacobian = AdvancedCalculusEngine.jacobian(
        lambda p: np.array([p[0] ** 2 + p[1], p[0] * p[1]]),
        point,
    )
    hessian = AdvancedCalculusEngine.hessian(
        lambda p: p[0] ** 2 + 3 * p[0] * p[1] + 2 * p[1] ** 2,
        point,
    )
    curve = AdvancedCalculusEngine.sample_curve(np.sin, 0.0, np.pi, samples=5)

    assert np.allclose(jacobian, [[4.0, 1.0], [3.0, 2.0]], atol=1e-7)
    assert np.allclose(hessian, [[2.0, 3.0], [3.0, 4.0]], atol=1e-5)
    assert curve.shape == (5, 2)
    assert curve[2, 1] == pytest.approx(1.0)


def test_linear_algebra_solves_system_and_returns_eigenpairs():
    matrix = np.array([[2.0, 0.0], [0.0, 3.0]])
    vector = np.array([4.0, 9.0])
    values, vectors = LinearAlgebraEngine.eigendecomposition(matrix)

    assert LinearAlgebraEngine.solve(matrix, vector) == pytest.approx([2.0, 3.0])
    assert matrix @ vectors == pytest.approx(vectors * values)
    with pytest.raises(ValueError, match="singular"):
        LinearAlgebraEngine.solve([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0])


def test_geometry_area_and_rotation_are_correct():
    assert GeometryEngine.polygon_area([[0, 0], [4, 0], [4, 3], [0, 3]]) == pytest.approx(12.0)
    assert GeometryEngine.rotate([1, 0], np.pi / 2) == pytest.approx([0, 1], abs=1e-12)
