"""Keep one QApplication alive for the entire GUI test session.

Creating short-lived Python QApplication wrappers in individual tests lets garbage
collection tear down Qt while another test is running a nested dialog event loop.
The desktop application itself already owns its QApplication until shutdown.
"""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope='session',autouse=True)
def qt_application():
    application=QApplication.instance() or QApplication([])
    yield application


@pytest.fixture(autouse=True)
def dispose_test_windows(qt_application):
    yield
    # A closed Qt window is hidden, not destroyed. Do not leave old event
    # filters/timers for Python GC to destroy inside a later modal event loop.
    import shiboken6
    for widget in qt_application.topLevelWidgets():
        if shiboken6.isValid(widget) and widget.parent() is None:
            shiboken6.delete(widget)
