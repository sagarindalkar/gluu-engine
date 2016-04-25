# gunicorn run
from crochet import setup as crochet_setup
from gluuapi.app import create_app
from gluuapi.log import configure_global_logging

from gluuapi.task import LicenseExpirationTask
from gluuapi.task import OxidpWatcherTask
from gluuapi.setup.signals import connect_setup_signals
from gluuapi.setup.signals import connect_teardown_signals

# normal run 
from gluuapi.cli import runserver
#from gluuapi.machine import Machine

# gunicorn run
def get_app_for_gunicorn():
    configure_global_logging()
    app = create_app()
    crochet_setup()

    if not app.debug:
        LicenseExpirationTask(app).perform_job()

    OxidpWatcherTask(app).perform_job()

    connect_setup_signals()
    connect_teardown_signals()
    return app

# gunicorn run
#app = get_app_for_gunicorn()
if __name__ == "__main__":
    runserver()
    # gunicorn run
    #app.run()

# HOW TO RUN
# $ DATA_DIR=$(pwd)/data python run.py

# run using gunicorn
# $ DATA_DIR=$(pwd)/data gunicorn run:app -b localhost:8080