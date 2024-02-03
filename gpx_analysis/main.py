"""
This script is the main entry point for the program
"""

# Import our own modules using this try-except structure to
# make sure it's always correctly imported
try:
    from gpx_analysis import app

except ImportError:
    import app


if __name__ == '__main__':
    my_app = app.GpxAnalysisApp()
    my_app.run_app()
