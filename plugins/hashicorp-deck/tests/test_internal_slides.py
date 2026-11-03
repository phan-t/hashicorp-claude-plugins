#!/usr/bin/env python3
"""Tests for Deck.internal() and Deck.hide().

    python3 plugins/hashicorp-deck/tests/test_internal_slides.py

Needs python-pptx, as the deck skill does, and is skipped without it.
"""

import sys
import tempfile
import unittest
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "skills" / "hashicorp-deck-htmltopptx" / "assets"
sys.path.insert(0, str(ASSETS))

try:
    from pptx import Presentation
    from hashicorp_deck import Deck
except ImportError:
    Deck = None


def hidden(slide):
    return slide._element.get("show") == "0"


@unittest.skipIf(Deck is None, "python-pptx not installed")
class InternalSlides(unittest.TestCase):
    def test_only_slides_inside_the_block_are_hidden(self):
        d = Deck()
        before = d.section("Shown")
        end = d.end()
        with d.internal():
            inside = [d.section("Internal"), d.titled("Cases")]
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

    def test_hide_one_slide(self):
        d = Deck()
        self.assertTrue(hidden(Deck.hide(d.section("Internal"))))


if __name__ == "__main__":
    unittest.main()
