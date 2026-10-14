"""Narrative scene authoring for cinematic mathematical storytelling.

This module turns the domain physics engine catalog into a coherent visual
story arc: setup, intuition, simulation, proof, and reveal. It is designed to
power elegant educational videos with a clear progression, like a strong
3Blue1Brown/Feynman-style explanation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


TEMPLATE_LIBRARY = {
    "pendulum": {
        "motif": "pivot, bob, and arc reveal",
        "palette": {"bg": "#0B0C10", "primary": "#F1C40F", "secondary": "#3498DB", "accent": "#FF4B4B"},
        "camera_notes": [
            "Start with a wide establishing angle and slowly push in toward the pivot.",
            "Then isolate the bob with a subtle zoom as the phase angle becomes clear.",
            "Finish with a wide shot and a clean energy overlay.",
        ],
        "visuals": [
            {"title": "setup", "engine": "mechanics", "element": "pendulum rig"},
            {"title": "intuition", "engine": "calculus", "element": "angular acceleration"},
            {"title": "simulation", "engine": "mechanics", "element": "damped trajectory"},
            {"title": "reveal", "engine": "waves", "element": "phase portrait"},
        ],
    },
    "wave interference": {
        "motif": "interference field with moving phase fronts",
        "palette": {"bg": "#0B0C10", "primary": "#00D2FF", "secondary": "#F1C40F", "accent": "#2ECC71"},
        "camera_notes": [
            "Use symmetric framing around the two sources.",
            "A slow lateral push reveals the amplitude modulation.",
            "End with a close-up on the nodal lines.",
        ],
        "visuals": [
            {"title": "setup", "engine": "waves", "element": "two source rings"},
            {"title": "intuition", "engine": "calculus", "element": "phase difference"},
            {"title": "simulation", "engine": "waves", "element": "interference map"},
            {"title": "reveal", "engine": "mechanics", "element": "energy transfer"},
        ],
    },
    "default": {
        "motif": "minimal diagram with elegant motion and a single explanatory lens",
        "palette": {"bg": "#0B0C10", "primary": "#F1C40F", "secondary": "#3498DB", "accent": "#FF4B4B"},
        "camera_notes": [
            "Establish the object with a quiet medium shot.",
            "Zoom in to the relevant feature and hold until the idea resolves.",
            "Finish on the invariant.",
        ],
        "visuals": [
            {"title": "setup", "engine": "mechanics", "element": "reference frame"},
            {"title": "intuition", "engine": "calculus", "element": "change law"},
            {"title": "simulation", "engine": "mechanics", "element": "trajectory"},
            {"title": "reveal", "engine": "geometry", "element": "invariant proof"},
        ],
    },
}


@dataclass(frozen=True)
class SceneBeat:
    """A single cinematic beat in a mathematical explanation."""

    title: str
    engine: str
    goal: str
    detail: str
    duration: float = 1.0


class NarrativeEngine:
    """Builds a compact narrative arc from the domain engine library."""

    _default_story = {
        "setup": (
            "mechanics",
            "Create the scene and define the core question.",
            "Introduce the phenomenon and its observables.",
        ),
        "intuition": (
            "calculus",
            "Translate the phenomenon into a model.",
            "Show the change law or slope that governs the motion.",
        ),
        "simulation": (
            "mechanics",
            "Run the deterministic simulation.",
            "Visualize the path and show the evolution under real dynamics.",
        ),
        "proof": (
            "geometry",
            "Confirm the structure with a geometric argument.",
            "Reveal the invariant or symmetry that explains the behavior.",
        ),
        "reveal": (
            "waves",
            "Lift the explanation into the general principle.",
            "Connect the local motion to the larger pattern.",
        ),
    }

    _motifs = {
        "wave": "interference field with moving phase fronts",
        "motion": "tracked path with a clean coordinate frame",
        "field": "charged particles with luminous vectors",
        "vector": "basis transformation with animated decomposition",
        "default": "minimal diagram with elegant motion and a single explanatory lens",
    }

    @staticmethod
    def build_story(topic: str, domains: Iterable[str] | None = None) -> list[SceneBeat]:
        """Build a coherent beat list for a scientific topic."""
        topic_name = str(topic or "general").strip().lower()
        chosen = list(domains) if domains is not None else ["mechanics", "calculus", "waves"]
        chosen = [str(name).strip().lower() for name in chosen if str(name).strip()]

        if not chosen:
            chosen = ["mechanics", "calculus", "waves"]

        beats: list[SceneBeat] = []
        default_items = list(NarrativeEngine._default_story.items())

        for index, (title, (engine, goal, detail)) in enumerate(default_items):
            beat_engine = engine if engine in chosen else chosen[index % len(chosen)]
            beats.append(
                SceneBeat(
                    title=title,
                    engine=beat_engine,
                    goal=goal,
                    detail=f"{topic_name.title()}: {detail}",
                    duration=1.2 + 0.5 * index,
                )
            )

        # A cinematic explanation is stronger when each beat adds a different lens.
        if len(beats) < 4:
            beats.append(
                SceneBeat(
                    title="resolution",
                    engine=chosen[0],
                    goal="Resolve the contradiction.",
                    detail=f"{topic_name.title()}: unify the intuition with the computation.",
                    duration=1.5,
                )
            )

        return beats

    @staticmethod
    def render_script(topic: str, domains: Iterable[str] | None = None) -> list[str]:
        """Convert a story into read-aloud narration cues."""
        beats = NarrativeEngine.build_story(topic, domains)
        script: list[str] = []
        for beat in beats:
            script.append(f"{beat.title}: {beat.goal} — {beat.detail}")
        return script

    @staticmethod
    def choose_domains(topic: str) -> list[str]:
        """Choose a balanced domain stack for a topic."""
        topic_key = topic.lower()
        if "wave" in topic_key:
            return ["waves", "mechanics", "calculus"]
        if "field" in topic_key or "electric" in topic_key or "magnet" in topic_key:
            return ["electrostatics", "magnetics", "geometry"]
        if "vector" in topic_key or "matrix" in topic_key:
            return ["linear_algebra", "geometry", "calculus"]
        if "orbit" in topic_key or "motion" in topic_key or "collision" in topic_key:
            return ["mechanics", "kinematics", "calculus"]
        return ["mechanics", "calculus", "waves"]

    @staticmethod
    def topic_blueprint(topic: str, domains: Iterable[str] | None = None) -> dict:
        """Return a production-ready storyboard blueprint for a topic."""
        topic_name = str(topic or "general").strip()
        domain_list = list(domains) if domains is not None else NarrativeEngine.choose_domains(topic_name)
        domain_list = [str(name).strip().lower() for name in domain_list if str(name).strip()]
        if not domain_list:
            domain_list = NarrativeEngine.choose_domains(topic_name)

        motif_key = "default"
        if "wave" in topic_name.lower():
            motif_key = "wave"
        elif "field" in topic_name.lower() or "electric" in topic_name.lower() or "magnet" in topic_name.lower():
            motif_key = "field"
        elif "vector" in topic_name.lower() or "matrix" in topic_name.lower():
            motif_key = "vector"
        elif "motion" in topic_name.lower() or "orbit" in topic_name.lower() or "collision" in topic_name.lower():
            motif_key = "motion"

        beats = NarrativeEngine.build_story(topic_name, domain_list)
        scene_plan = [
            {
                "title": beat.title,
                "engine": beat.engine,
                "goal": beat.goal,
                "detail": beat.detail,
                "duration": beat.duration,
            }
            for beat in beats
        ]
        voiceover = [
            f"{beat.title.capitalize()}: {beat.goal} {beat.detail}."
            for beat in beats
        ]
        base_template = TEMPLATE_LIBRARY.get(topic_name.lower(), TEMPLATE_LIBRARY["default"])
        return {
            "topic": topic_name,
            "domains": domain_list,
            "motif": base_template["motif"],
            "scene_plan": scene_plan,
            "voiceover": voiceover,
            "style": "elegant, minimal, mathematically precise, cinematic",
            "palette": base_template["palette"],
            "camera_notes": base_template["camera_notes"],
            "visuals": [
                {
                    "title": entry["title"],
                    "engine": entry["engine"],
                    "element": entry["element"],
                }
                for entry in base_template["visuals"]
            ],
        }

    @staticmethod
    def build_episode(topic: str, domains: Iterable[str] | None = None) -> dict:
        """Build a polished cinematic episode blueprint with runtime and direction."""
        plan = NarrativeEngine.topic_blueprint(topic, domains)
        runtime_seconds = sum(float(beat["duration"]) for beat in plan["scene_plan"])
        topic_key = str(topic or "general").lower()
        key_equations = []
        if "wave" in topic_key:
            key_equations = [r"y(x,t)=A \sin(kx-\omega t+\phi)", r"v = \lambda f"]
        elif "pend" in topic_key:
            key_equations = [r"\theta'' + \frac{g}{L}\sin\theta = 0", r"E = \frac{1}{2}mL^2\dot{\theta}^2 + mgL(1 - \cos\theta)"]
        elif "field" in topic_key or "electric" in topic_key or "magnet" in topic_key:
            key_equations = [r"F = q(E + v \times B)", r"\nabla \cdot E = \rho / \epsilon_0"]
        else:
            key_equations = [r"f'(x) = \lim_{h\to 0} \frac{f(x+h)-f(x)}{h}", r"A x = b"]

        core_idea = {
            "pendulum": "The restoring force is not linear at large angles; the geometry of the arc and the conservation of energy explain the motion.",
            "wave interference": "Interference is the sum of phases, and the geometry of phase difference creates brightness and darkness.",
        }.get(topic_key, "A small number of invariants and local rules creates the whole structure of the motion.")

        intuition_lines = [
            "Look at the local change, not the whole trajectory at once.",
            "Every beautiful formula is a compressed story about symmetry and balance.",
            "The deep idea is the invariant hidden inside the motion.",
        ]

        return {
            **plan,
            "core_idea": core_idea,
            "key_equations": key_equations,
            "intuition": intuition_lines,
            "physical_deepness": [
                "The model follows the minimal laws that survive the geometry of the problem.",
                "The animation should reveal structure before numbers, and numbers before abstraction.",
                "The final image should feel inevitable, not merely decorative.",
            ],
            "runtime_seconds": runtime_seconds,
            "camera_notes": plan["camera_notes"],
            "visuals": plan["visuals"],
            "narration_style": "slow, precise, luminous, explanatory",
        }
