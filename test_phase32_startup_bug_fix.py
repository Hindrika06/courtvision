"""
Phase 32 Regression Test — Production Startup Bug Fix.

Root cause: tk.Label was constructed with `px=` and `py=` keyword arguments,
which are NOT valid Tkinter options. Tkinter/Tcl raises:
    _tkinter.TclError: unknown option "-px"

The correct Tkinter keyword arguments for internal padding are `padx=` and `pady=`.

This test verifies that both affected widgets in ui/main_window.py can be
constructed without raising _tkinter.TclError.
"""
import unittest
import tkinter as tk


class TestPhase32StartupBugFix(unittest.TestCase):
    """Regression tests for the -px / -py TclError startup crash (Phase 32)."""

    def setUp(self):
        """Create a hidden Tk root for widget construction tests."""
        self.root = tk.Tk()
        self.root.withdraw()  # Keep the window hidden during tests

    def tearDown(self):
        """Destroy the Tk root after each test."""
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_status_badge_padx_pady_valid(self):
        """
        Verify that the status_badge Label (line 191 in main_window.py)
        can be created with padx= and pady= without raising TclError.

        Bug: px=12, py=4 raised _tkinter.TclError: unknown option "-px"
        Fix: padx=12, pady=4
        """
        try:
            badge = tk.Label(
                self.root,
                text="● DISCONNECTED",
                font=("Segoe UI", 10, "bold"),
                bg="#444444",
                fg="#ffffff",
                padx=12,
                pady=4,
            )
            # Widget must exist and be a Label
            self.assertIsInstance(badge, tk.Label)
        except tk.TclError as e:
            self.fail(
                f"tk.Label raised TclError with padx=/pady=: {e}\n"
                "This indicates the -px bug regression has returned."
            )

    def test_status_badge_invalid_px_raises(self):
        """
        Confirm that the original broken code (px=, py=) does raise TclError.
        This validates our test environment correctly detects the bug.
        """
        with self.assertRaises(tk.TclError):
            # This is the original broken code — must raise TclError
            _bad = tk.Label(
                self.root,
                text="● DISCONNECTED",
                font=("Segoe UI", 10, "bold"),
                bg="#444444",
                fg="#ffffff",
                px=12,
                py=4,
            )

    def test_warn_label_pady_valid(self):
        """
        Verify that the warning banner Label (line 209 in main_window.py)
        can be created with pady= without raising TclError.

        Bug: py=2 raised _tkinter.TclError: unknown option "-py"
        Fix: pady=2
        """
        try:
            warn_lbl = tk.Label(
                self.root,
                text="Note: CourtVision requires a fixed camera position per court. Recalibrate if camera moves.",
                bg="#2a2010",
                fg="#ffbb33",
                font=("Segoe UI", 8, "italic"),
                pady=2,
            )
            self.assertIsInstance(warn_lbl, tk.Label)
        except tk.TclError as e:
            self.fail(
                f"tk.Label raised TclError with pady=: {e}\n"
                "This indicates the -py bug regression has returned."
            )

    def test_warn_label_invalid_py_raises(self):
        """
        Confirm that the original broken code (py=) does raise TclError.
        """
        with self.assertRaises(tk.TclError):
            _bad = tk.Label(
                self.root,
                text="Warning",
                bg="#2a2010",
                fg="#ffbb33",
                py=2,
            )

    def test_main_window_source_no_px_py_options(self):
        """
        Scan ui/main_window.py for any remaining px= or py= kwargs
        that could cause a TclError at runtime.
        """
        import re
        import os

        main_window_path = os.path.join(
            os.path.dirname(__file__), "ui", "main_window.py"
        )
        self.assertTrue(
            os.path.exists(main_window_path),
            f"ui/main_window.py not found at {main_window_path}",
        )

        with open(main_window_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Match 'px=' or 'py=' as keyword arguments (word boundary to avoid
        # matching 'padx=' or 'pady=' which are valid)
        invalid_pattern = re.compile(r'\b(?<!pad)(px|py)=')
        matches = [(i + 1, line.strip()) for i, line in enumerate(content.splitlines())
                   if invalid_pattern.search(line)]

        self.assertEqual(
            matches, [],
            f"Found invalid px=/py= options in ui/main_window.py:\n"
            + "\n".join(f"  Line {ln}: {txt}" for ln, txt in matches)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
