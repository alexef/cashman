#!/usr/bin/env python

from flask.ext.script import Manager
from cashman.app import create_app
from cashman.models import db_manager

app = create_app()
manager = Manager(app)

manager.add_command('db', db_manager)

if __name__ == '__main__':
    manager.run()
