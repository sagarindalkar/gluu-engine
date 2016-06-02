# gunicorn run
# from crochet import setup as crochet_setup
# from gluuengine.app import create_app
# from gluuengine.log import configure_global_logging

# gunicorn run
# from gluuengine.task import LicenseExpirationTask
# from gluuengine.task import OxidpWatcherTask
# from gluuengine.setup.signals import connect_setup_signals
# from gluuengine.setup.signals import connect_teardown_signals

# normal run
from gluuengine.cli import runserver2
#from gluuengine.machine import Machine


# def get_app_for_gunicorn():
#     configure_global_logging()
#     app = create_app()
#     crochet_setup()

#     if not app.debug:
#         LicenseExpirationTask(app).perform_job()

#     OxidpWatcherTask(app).perform_job()

#     connect_setup_signals()
#     connect_teardown_signals()
#     return app

# gunicorn run
#app = get_app_for_gunicorn()
if __name__ == "__main__":
    # m = Machine()
    # data = m.is_running('keyval')
    # print type(data)
    # print data
    runserver2()
    # gunicorn run
    #app.run()

# HOW TO RUN
# $ LOG_DIR=/tmp DATA_DIR=$(pwd)/data python run.py

# run using gunicorn
# $ DATA_DIR=$(pwd)/data gunicorn run:app -b localhost:8080
