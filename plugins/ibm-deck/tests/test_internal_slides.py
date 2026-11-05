#!/usr/bin/env python3
"""Tests for Deck.internal() and Deck.hide().

    python3 plugins/ibm-deck/tests/test_internal_slides.py

Needs python-pptx, as the deck skill does, and is skipped without it.
"""

import sys
import tempfile
import unittest
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "skills" / "ibm-deck-htmltopptx" / "assets"
sys.path.insert(0, str(ASSETS))

# Only python-pptx is optional. An ImportError from the deck module itself is a real
# failure, so it is left to fail the run rather than skip every test.
try:
    from pptx import Presentation
except ImportError:
    Presentation = None
else:
    from ibm_deck import Deck


def hidden(slide):
    return slide._element.get("show") == "0"


@unittest.skipIf(Presentation is None, "python-pptx not installed")
class InternalSlides(unittest.TestCase):
    def test_only_slides_inside_the_block_are_hidden(self):
        d = Deck()
        before = d.section("Shown")
        end = d.end()
        with d.internal():
            inside = [d.section("Internal"), d.section("Cases")]
        after = d.section("Shown again")
        self.assertFalse(hidden(before) or hidden(end) or hidden(after))
        self.assertTrue(all(hidden(s) for s in inside))

    def test_hidden_survives_save(self):
        d = Deck()
        d.end()
        with d.internal():
            d.section("Internal")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deck.pptx"
            d.save(path)
            slides = Presentation(str(path)).slides
            self.assertEqual([hidden(s) for s in slides], [False, True])

    def test_block_resets_after_an_error(self):
        d = Deck()
        with self.assertRaises(RuntimeError), d.internal():
            raise RuntimeError
        self.assertFalse(hidden(d.section("Shown")))

    def test_drop_internal_leaves_hidden_slides_out_of_the_file(self):
        d = Deck()
        d.section("Shown")
        d.end()
        with d.internal():
            d.section("Internal")
        Deck.hide(d.section("Hidden by hand"))
        with tempfile.TemporaryDirectory() as tmp:
            sent = Path(tmp) / "sent.pptx"
            kept = Path(tmp) / "kept.pptx"
            d.save(sent, drop_internal=True)
            d.save(kept)
            self.assertEqual(len(Presentation(str(sent)).slides), 2)
            self.assertFalse(any(hidden(s) for s in Presentation(str(sent)).slides))
            self.assertEqual([hidden(s) for s in Presentation(str(kept)).slides],
                             [False, False, True, True])

    def test_hide_one_slide(self):
        d = Deck()
        self.assertTrue(hidden(Deck.hide(d.section("Internal"))))


if __name__ == "__main__":
    unittest.main()
