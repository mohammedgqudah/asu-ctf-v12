import os
from celery import Celery, Task
from flask import Flask
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BROKER_BASE = os.path.join(BASE_DIR, "broker")

broker_opts = {
    "data_folder_in": os.path.join(BROKER_BASE, "queue"),
    "data_folder_out": os.path.join(BROKER_BASE, "queue"),
    "data_folder_processed": os.path.join(BROKER_BASE, "processed"),
    "control_folder": os.path.join(BROKER_BASE, "control"),
}

for path in broker_opts.values():
    os.makedirs(path, exist_ok=True)


def celery_init_app(flask_app: Flask) -> Celery:
    class ContextTask(Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    flask_app.config.from_mapping(
        SECRET_KEY=secrets.token_hex(32),
        CELERY={
            "broker_url": "filesystem://",
            "result_backend": None,
            "task_ignore_result": True,
            "accept_content": ["pickle", "json"],
            "broker_transport_options": broker_opts,
            "beat_schedule": {
                "check_links_every_5": {"task": "main.check_links", "schedule": 10}
            },
        },
    )
    celery = Celery(
        flask_app.import_name,
        broker=flask_app.config["CELERY"]["broker_url"],
        task_cls=ContextTask,
    )
    celery.conf.update(flask_app.config["CELERY"])
    celery.conf.broker_transport_options = flask_app.config["CELERY"][
        "broker_transport_options"
    ]

    return celery
