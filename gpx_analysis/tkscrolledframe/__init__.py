"""A scrollable Frame widget for Tkinter."""

try:
    from tkscrolledframe.widget import ScrolledFrame
except ImportError:
    from widget import ScrolledFrame

# The only thing we need to publicly export is the widget
__all__ = ["ScrolledFrame"]
