"""Build Little Claude as a standalone macOS app.

Usage:
    pip install py2app
    python setup.py py2app

The app will be created in dist/Little Claude.app
"""

from setuptools import setup

APP = ['app.py']
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'CFBundleName': 'Little Claude',
        'CFBundleDisplayName': 'Little Claude',
        'CFBundleIdentifier': 'com.katemptiness.littleclaude',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,  # No Dock icon (the crab IS on the Dock)
    },
    'packages': ['sprites'],
}

setup(
    name='Little Claude',
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
