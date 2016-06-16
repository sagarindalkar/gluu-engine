from gluuengine.cli import runserver2

if __name__ == "__main__":
    runserver2()

# # HOW TO RUN
# # $ LOG_DIR=/tmp/gluulog DATA_DIR=/tmp/gluudata python run.py


#-------------------------------------------------------------------------------

# gunicorn run
# from crochet import setup as crochet_setup
# from gluuengine.app import create_app
# from gluuengine.log import configure_global_logging
# from gluuengine.setup.signals import connect_setup_signals
# from gluuengine.setup.signals import connect_teardown_signals


# def get_app_for_gunicorn():
#     configure_global_logging()
#     app = create_app()
#     crochet_setup()

#     connect_setup_signals()
#     connect_teardown_signals()
#     return app

# app = get_app_for_gunicorn()

# run using gunicorn
# $ gunicorn run:app -b localhost:8080 -e LOG_DIR=/tmp/gluulog,DATA_DIR=/tmp/gluudata
