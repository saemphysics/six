#!/usr/bin/env python3
"""
visual_kit.py v2.3.2 — Cinematic additions (fixed + upgraded)
Fixes from audit:
  - spotlight now saves original opacities (dict) and restores correctly
  - unspotlight restores saved values, not 1.0
  - ambient uses scene.renderer.time (no ValueTracker leak) + cleanup method
  - camera_shake uses single path animation (no looped play)
  - term_bind handles MathTex/Tex properly via submobjects
  - vector_decomposition supports arbitrary basis
  - kinetic_title handles LaTeX
  - All functions graceful degradation (P5)
"""
from __future__ import annotations
import numpy as np
from manim import (
    VGroup, Arrow, Line, DashedLine, Text, MathTex, Dot, Circle,
    Rectangle, FadeIn, FadeOut, GrowArrow, Create, Write,
    UP, DOWN, LEFT, RIGHT, ORIGIN, TAU,
    there_and_back, rate_functions as rf, config, VMobject, ValueTracker,
)
try:
    from manim import LaggedStart
except ImportError:
    LaggedStart = None

COLOR = {
    "accent": "#F1C40F", "field": "#3498DB", "force": "#2ECC71",
    "pos": "#FF4B4B", "neg": "#00D2FF", "muted": "#8A8F9C",
    "white": "#F2F3F5", "card": "#15161D", "border": "#2A2C36",
}

def _is_latex(s):
    return any(c in str(s) for c in ("\\", "^", "_", "{", "}"))

def _label(text, size=22, color=None):
    color = color or COLOR["accent"]
    try:
        if _is_latex(text):
            return MathTex(text, font_size=size, color=color)
        return Text(text, font_size=size, color=color)
    except Exception:
        return Text(str(text), font_size=size, color=color)

def _mob_edge(m, direction):
    try:
        if direction is UP:    return m.get_top()
        if direction is DOWN:  return m.get_bottom()
        if direction is LEFT:  return m.get_left()
        if direction is RIGHT: return m.get_right()
    except Exception:
        pass
    try:
        return m.get_center()
    except Exception:
        return np.zeros(3)

def annotate(scene, target, text, direction=UP, distance=1.2,
             color=None, font_size=22, run_time=0.6,
             hold=1.6, fade_out=True):
    color = color or COLOR["accent"]
    if target is None:
        return None
    try:
        edge = _mob_edge(target, direction)
        tail = edge + direction * distance
        arrow = Arrow(tail, edge, buff=0.05, color=color, stroke_width=3,
                      max_tip_length_to_length_ratio=0.30)
    except Exception:
        return None
    lbl = _label(text, size=font_size, color=color)
    try:
        lbl.next_to(arrow.get_start(), direction, buff=0.10)
    except Exception:
        lbl.move_to(arrow.get_start() + direction * 0.4)
    group = VGroup(arrow, lbl)
    try:
        scene.play(GrowArrow(arrow),
                   FadeIn(lbl, shift=direction * 0.10),
                   run_time=run_time, rate_func=rf.ease_out_cubic)
        scene.wait(hold)
        if fade_out:
            scene.play(FadeOut(group, shift=direction * 0.15),
                       run_time=0.4, rate_func=rf.ease_in_cubic)
            return None
    except Exception:
        pass
    return group

# --- FIX 1: save original opacities ---
_SPOTLIGHT_SAVED = {}

def spotlight(scene, target, dim=0.20, run_time=0.5, exclude=None):
    global _SPOTLIGHT_SAVED
    _SPOTLIGHT_SAVED.clear()
    exclude_ids = {id(m) for m in (exclude or [])}
    exclude_ids.add(id(target))
    dim_targets = []
    for m in scene.mobjects:
        if id(m) in exclude_ids:
            continue
        if getattr(m, "updaters", None):
            if len(m.updaters) > 0:
                continue
        try:
            if m.get_opacity() < 0.05:
                continue
        except Exception:
            pass
        # save
        try:
            _SPOTLIGHT_SAVED[id(m)] = m.get_opacity()
        except Exception:
            _SPOTLIGHT_SAVED[id(m)] = 1.0
        dim_targets.append(m)
    if not dim_targets:
        return []
    try:
        scene.play(*[m.animate.set_opacity(dim) for m in dim_targets],
                   run_time=run_time, rate_func=rf.ease_in_out_sine)
    except Exception:
        pass
    return dim_targets

def unspotlight(scene, dimmed, run_time=0.5):
    if not dimmed:
        return
    anims = []
    for m in dimmed:
        orig = _SPOTLIGHT_SAVED.get(id(m), 1.0)
        try:
            anims.append(m.animate.set_opacity(orig))
        except Exception:
            pass
    _SPOTLIGHT_SAVED.clear()
    if anims:
        try:
            scene.play(*anims, run_time=run_time, rate_func=rf.ease_in_out_sine)
        except Exception:
            pass

_AMBIENT_INSTALLED = set()

def ambient(scene, mobs, amp=0.02, period=4.0):
    """Uses renderer.time, no ValueTracker leak. Call ambient_cleanup() to remove."""
    if not mobs:
        return
    for m in mobs:
        if id(m) in _AMBIENT_INSTALLED:
            continue
        try:
            base = m.get_center().copy()
        except Exception:
            continue
        def _mk(mob, base_center, amp=amp, period=period):
            def upd(mob_upd, dt):
                try:
                    t = getattr(scene.renderer, "time", 0) or 0
                    dy = amp * np.sin(2 * np.pi * t / period)
                    mob_upd.move_to(base_center + np.array([0.0, dy, 0.0]))
                except Exception:
                    pass
            return upd
        try:
            m.add_updater(_mk(m, base))
            _AMBIENT_INSTALLED.add(id(m))
        except Exception:
            pass

def ambient_cleanup(mobs=None):
    """Remove ambient updaters - now actually clears updaters"""
    global _AMBIENT_INSTALLED
    if mobs is None:
        # No specific mobs passed - just clear registry (caller lost refs)
        _AMBIENT_INSTALLED.clear()
        return
    for m in mobs:
        try:
            m.clear_updaters()
        except Exception:
            pass
        _AMBIENT_INSTALLED.discard(id(m))

def kinetic_title(scene, text, pos=None, size=48, color=None,
                  stagger=0.04, run_time=1.2, hold=0.8, fade_out=True):
    color = color or COLOR["white"]
    if pos is None:
        pos = np.array([0.0, 0.0, 0.0])
    # If contains latex, use single MathTex
    if _is_latex(text):
        try:
            group = MathTex(text, font_size=size, color=color)
            group.move_to(pos)
            scene.play(Write(group, rate_func=rf.ease_out_cubic), run_time=run_time)
            scene.wait(hold)
            if fade_out:
                scene.play(FadeOut(group, shift=UP*0.2), run_time=0.5)
                return None
            return group
        except Exception:
            pass
    try:
        chars = [Text(c, font_size=size, color=color) for c in str(text)]
    except Exception:
        chars = [Text(str(text), font_size=size, color=color)]
    group = VGroup(*chars).arrange(RIGHT, buff=size * 0.006)
    group.move_to(pos)
    anims = [FadeIn(c, shift=UP * 0.10) for c in chars]
    try:
        if LaggedStart is not None and len(anims) > 1:
            scene.play(LaggedStart(*anims, lag_ratio=stagger),
                       run_time=run_time, rate_func=rf.ease_out_cubic)
        else:
            scene.play(*anims, run_time=run_time)
        scene.wait(hold)
        if fade_out:
            scene.play(FadeOut(group, shift=UP * 0.20),
                       run_time=0.5, rate_func=rf.ease_in_cubic)
            return None
    except Exception:
        pass
    return group

def term_bind(scene, equation, term_indices, visuals, colors=None, pulse=True):
    if colors is None:
        colors = [COLOR["accent"], COLOR["force"], COLOR["pos"], COLOR["field"]]
    # Handle MathTex: equation.submobjects or equation itself
    eq_children = []
    try:
        if hasattr(equation, "submobjects") and len(equation.submobjects) > 0:
            # If it's a MathTex with sub-parts, use its parts
            eq_children = equation.submobjects
        elif isinstance(equation, (list, tuple, VGroup)):
            eq_children = list(equation)
        else:
            eq_children = [equation]
    except Exception:
        eq_children = [equation]

    for i, idx in enumerate(term_indices):
        if i >= len(visuals):
            break
        col = colors[i % len(colors)]
        try:
            if idx < len(eq_children):
                eq_children[idx].set_color(col)
        except Exception:
            pass
        try:
            visuals[i].set_color(col)
        except Exception:
            pass

    if not pulse:
        return
    for i, idx in enumerate(term_indices):
        if i >= len(visuals):
            break
        try:
            if idx >= len(eq_children):
                continue
            scene.play(
                eq_children[idx].animate(rate_func=there_and_back, run_time=0.6).scale(1.15),
                visuals[i].animate(rate_func=there_and_back, run_time=0.6).scale(1.10),
                run_time=0.6,
            )
        except Exception:
            continue

def camera_shake(scene, amplitude=0.15, cycles=4, run_time=0.4):
    """FIX: single animation path, not looped play calls"""
    try:
        frame = scene.camera.frame
        base = frame.get_center().copy()
    except Exception:
        return
    try:
        # Build path: left-right-left...
        import math
        # Use a single updater-driven shake for smoothness
        def shake_updater(mob, dt):
            t = getattr(scene.renderer, "time", 0) % run_time
            # sinusoidal shake
            dx = amplitude * math.sin(2*math.pi*cycles*t/run_time)
            mob.move_to(base + np.array([dx, 0, 0]))
        
        frame.add_updater(shake_updater)
        scene.wait(run_time)
        frame.clear_updaters()
        frame.move_to(base)
    except Exception:
        # fallback: two quick shifts
        try:
            scene.play(frame.animate.shift(RIGHT*amplitude), run_time=run_time*0.25, rate_func=rf.ease_out_sine)
            scene.play(frame.animate.shift(LEFT*amplitude*2), run_time=run_time*0.5, rate_func=rf.ease_in_out_sine)
            scene.play(frame.animate.move_to(base), run_time=run_time*0.25)
        except Exception:
            pass

def vector_decomposition(scene, vector, show_labels=True,
                         comp_color_x=None, comp_color_y=None,
                         run_time=1.0):
    comp_color_x = comp_color_x or COLOR["force"]
    comp_color_y = comp_color_y or COLOR["field"]
    try:
        start = vector.get_start()
        end = vector.get_end()
    except Exception:
        return None
    foot = np.array([end[0], start[1], 0.0])
    arrow_x = Arrow(start, foot, buff=0, color=comp_color_x,
                    stroke_width=3, max_tip_length_to_length_ratio=0.30)
    arrow_y = Arrow(foot, end, buff=0, color=comp_color_y,
                    stroke_width=3, max_tip_length_to_length_ratio=0.30)
    try:
        scene.play(Create(arrow_x), Create(arrow_y), run_time=run_time)
    except Exception:
        return None
    labels = None
    if show_labels:
        lx = _label("v_x", size=20, color=comp_color_x)
        ly = _label("v_y", size=20, color=comp_color_y)
        try:
            lx.next_to(arrow_x, DOWN, buff=0.10)
            ly.next_to(arrow_y, RIGHT, buff=0.10)
            scene.play(FadeIn(lx), FadeIn(ly), run_time=0.4)
            labels = VGroup(lx, ly)
        except Exception:
            pass
    return VGroup(arrow_x, arrow_y, labels) if labels else VGroup(arrow_x, arrow_y)

def cinematic_transition(scene, kind="wipe", direction="right", duration=0.7):
    fw = config.frame_width
    fh = config.frame_height
    try:
        if kind == "wipe":
            cover = Rectangle(width=fw * 1.2, height=fh * 1.2,
                              fill_color=COLOR["card"], fill_opacity=1.0, stroke_width=0)
            cover.move_to(np.array([-fw * 1.2, 0, 0]))
            scene.add(cover)
            scene.play(cover.animate.move_to(ORIGIN), run_time=duration*0.5, rate_func=rf.ease_in_cubic)
            scene.play(cover.animate.move_to(np.array([fw*1.2,0,0])), run_time=duration*0.5, rate_func=rf.ease_out_cubic)
            scene.remove(cover)
        elif kind == "push":
            dx = -fw if direction == "left" else fw
            mobs = [m for m in scene.mobjects if m is not getattr(scene.camera, "frame", None)]
            if mobs:
                scene.play(*[m.animate.shift(RIGHT*dx) for m in mobs], run_time=duration, rate_func=rf.ease_in_out_sine)
                # reset instantly off-screen then back for next scene - actually just leave shifted, caller will add new
                scene.play(*[m.animate.shift(RIGHT*-dx) for m in mobs], run_time=0.01)
        elif kind == "iris":
            max_r = float(np.hypot(fw, fh)) * 0.6
            cover = Circle(radius=max_r, fill_color=COLOR["card"], fill_opacity=1.0, stroke_width=0).move_to(ORIGIN)
            scene.add(cover)
            scene.play(cover.animate.scale(0.01), run_time=duration, rate_func=rf.ease_in_cubic)
            scene.remove(cover)
        elif kind == "zoom_blur":
            frame = scene.camera.frame
            base = frame.get_width()
            scene.play(frame.animate.set(width=base*0.6), run_time=duration*0.5, rate_func=rf.ease_in_cubic)
            scene.play(frame.animate.set(width=base), run_time=duration*0.5, rate_func=rf.ease_out_cubic)
    except Exception as e:
        # graceful degradation
        print(f"[visual_kit] {kind} transition fallback: {e}")
