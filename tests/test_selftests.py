"""pytest entry points wrapping selib's in-module self-tests (the same checks run
on the fleet box). jax-dependent tests are skipped if jax is unavailable."""
import importlib
import pytest


def test_calc_selftest():
    from selib import calc
    calc._selftest()


def test_seopt_selftest():
    from selib import seopt
    seopt._selftest()


def test_htree_selftest():
    from selib import htree
    htree._selftest()


def test_segnn_selftest():
    if importlib.util.find_spec("jax") is None:
        pytest.skip("jax not installed (optional [gnn] extra)")
    from selib import segnn
    segnn._selftest()


def test_smoke():
    from tests.test_smoke import test_smoke as smoke
    smoke()
