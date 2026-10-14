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


def test_advanced_calculus_directional_derivative_arc_length_and_line_integral():
    point = np.array([3.0, 4.0])
    derivative = AdvancedCalculusEngine.directional_derivative(
        lambda p: p[0] ** 2 + p[1] ** 2,
        point,
        [3.0, 4.0],
    )
    circle = lambda t: np.column_stack((np.cos(t), np.sin(t)))
    circumference = AdvancedCalculusEngine.arc_length(circle, 0.0, 2 * np.pi, samples=4000)
    circulation = AdvancedCalculusEngine.line_integral(
        lambda p: np.array([-p[1], p[0]]),
        circle,
        0.0,
        2 * np.pi,
        samples=4000,
    )

    assert derivative == pytest.approx(10.0)
    assert circumference == pytest.approx(2 * np.pi, rel=1e-6)
    assert circulation == pytest.approx(2 * np.pi, rel=1e-6)


def test_geometry_centroid_and_affine_transform_support_animation_coordinates():
    vertices = np.array([[0, 0], [4, 0], [4, 3], [0, 3]], dtype=float)
    centroid = GeometryEngine.polygon_centroid(vertices)
    transformed = GeometryEngine.affine_transform(
        vertices,
        [[0, -1], [1, 0]],
        translation=[2, 1],
    )

    assert centroid == pytest.approx([2.0, 1.5])
    assert transformed[0] == pytest.approx([2.0, 1.0])
    assert GeometryEngine.polygon_area(transformed) == pytest.approx(12.0)


def test_linear_algebra_least_squares_and_matrix_animation_samples():
    matrix = np.array([[1.0, 0.0], [1.0, 1.0], [1.0, 2.0]])
    solution = LinearAlgebraEngine.least_squares(matrix, [1.0, 3.0, 5.0])
    frames = LinearAlgebraEngine.sample_matrix_interpolation(
        np.eye(2),
        np.array([[2.0, 1.0], [0.0, 3.0]]),
        samples=5,
    )

    assert solution == pytest.approx([1.0, 2.0])
    assert frames.shape == (5, 2, 2)
    assert frames[0] == pytest.approx(np.eye(2))
    assert np.allclose(frames[-1], [[2.0, 1.0], [0.0, 3.0]])
