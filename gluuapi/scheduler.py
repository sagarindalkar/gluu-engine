# The MIT License (MIT)
#
# Copyright (c) 2015 Gluu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import os
import logging

import redislite.patch
redislite.patch.patch_redis()

from apscheduler.schedulers.background import BackgroundScheduler as _Scheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.executors.base import run_job
from flask import _app_ctx_stack
from pytz import utc

logging.getLogger(__name__)


def _run_job_with_ctx(app, job, jobstore_alias, run_times, logger_name):
    """Runs job with app context.
    """
    with app.app_context():
        return run_job(job, jobstore_alias, run_times, logger_name)


def _create_scheduler(app):
    jobstores = {
        "default": {
            "type": "redis",
            "dbfilename": app.config["SCHEDULE_DATABASE_URI"],
        },
    }

    job_defaults = {
        "coalesce": False,
        "max_instances": 3,
    }

    executors = {
        "default": ContextExecutor(app=app),
    }
    scheduler = _Scheduler(
        jobstores=jobstores,
        job_defaults=job_defaults,
        executors=executors,
        timezone=utc,
    )
    return scheduler


class ContextExecutor(ThreadPoolExecutor):
    def __init__(self, max_workers=10, app=None):
        self.app = app
        super(ContextExecutor, self).__init__(max_workers=max_workers)

    def _do_submit_job(self, job, run_times):
        def callback(f):
            if hasattr(f, "exception_info"):
                exc, tb = f.exception_info()
            else:
                exc, tb = f.exception(), getattr(f.exception(), '__traceback__', None)

            if exc:
                self._run_job_error(job.id, exc, tb)
            else:
                self._run_job_success(job.id, f.result())

        f = self._pool.submit(_run_job_with_ctx, self.app, job,
                              job._jobstore_alias, run_times,
                              self._logger.name)
        f.add_done_callback(callback)


class Scheduler(object):
    def __init__(self, app=None):
        self._scheduler = None
        self.app = app

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault("SCHEDULE_DATABASE_URI", "")
        app.extensions = getattr(app, "extensions", {})
        app.extensions["scheduler"] = self

    def _get_app(self):
        if self.app:
            return self.app

        ctx = _app_ctx_stack.top
        if ctx:
            return ctx.app

        raise RuntimeError("application not registered on scheduler "
                           "instance and no application bound "
                           "to current context")

    @property
    def scheduler(self):
        if not self._scheduler:
            app = self._get_app()

            if not os.path.exists(app.config["SCHEDULE_DATABASE_URI"]):
                try:
                    os.makedirs(
                        os.path.dirname(app.config["SCHEDULE_DATABASE_URI"])
                    )
                except OSError:
                    pass
            self._scheduler = _create_scheduler(app)
        return self._scheduler

    def add_job(self, *args, **kwargs):
        """Adds job to be executed in background process.

        Note, calling this method requires app context.
        """
        return self.scheduler.add_job(*args, **kwargs)

    def start(self):
        """Runs the scheduler in background process.

        Note, calling this method requires app context.
        """
        self.scheduler.start()


# Shortcut to Scheduler
scheduler = Scheduler()
