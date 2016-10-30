# -*- encoding: utf-8 -*-
from __future__ import with_statement
from datetime import datetime
from fabric.api import env, require, run, sudo
from fabric.context_managers import cd
from fabric.contrib.files import append, contains, exists
import os
import time




# Servers

def prod():
    env.config = 'PROD'
    env.hosts = ['bagofgold.com.br']
    env.path = '/bagogold'
    env.repository = 'https://bitbucket.org/nizbel/bag-of-gold'
    env.user = 'bagofgold'
    env.virtualenv = 'bagogold'
    env.virtualenv_path = '/home/bagofgold/.virtualenvs/bagogold'
#     env.procs = ['nginx', 'site', 'winfinity']

# Actions

# def setup():
#     require('path')
#     require('repository')
#     require('config')
#     
#     # Setup virtualenv and virtualenvwrapper
#     # NOTE: pip must already be installed on the system
#     sudo('pip install virtualenv virtualenvwrapper', shell=False)
#     if not exists('~/.profile'):
#         run('touch ~/.profile')
#     if not exists('~/.virtualenvs'):
#         run('mkdir ~/.virtualenvs')
#     if not contains('WORKON_HOME', '~/.profile'):
#         append(('\nexport WORKON_HOME=$HOME/.virtualenvs'
#                 '\nsource /usr/local/bin/virtualenvwrapper.sh'), '~/.profile')
#         run('source ~/.profile')
# 
#     # Create the virtualenv
#     run('mkvirtualenv %(virtualenv)s' % env)
# 
#     # Clone the repository
#     if not exists(env.path):
#         run('hg clone %(repository)s %(path)s' % env)


# def update(requirements=False, rev=None):
#     require('path')
#     require('virtualenv')
#     env.warn_only = True
# 
#     requirements = _to_bool(requirements)
#     rev = rev
# 
#     sudo('/etc/init.d/supervisor stop')
#     run('sleep 10')
#     
#     # Backup first... always!
#     if env.config == 'prod':
#         backup_db()
#         
#     # Update the code
#     with cd(env.path):
#         run('find . -name "*.pyc" | xargs rm')
#         if rev:
#             run('workon %(virtualenv)s; hg pull; hg update -r %(rev)s' % {'virtualenv': env.virtualenv, 'rev': rev})
#         else:
#             run('workon %(virtualenv)s; hg pull; hg update' % {'virtualenv': env.virtualenv})
#         if requirements:
#             run('workon %(virtualenv)s; pip install -U -r requirements.stable.txt' % env)
# 
#         # Syncdb, migrate, and sync extensions
#         run('workon %(virtualenv)s; python manage.py syncdb --migrate --noinput' % env)
#         run('workon %(virtualenv)s; python manage.py syncext' % env)
#         
#         # Collect static files
#         run('workon %(virtualenv)s; python manage.py collectstatic --noinput' % env)
#         run('workon %(virtualenv)s; python manage.py collectstatic --settings=winfinity.settings_sites --noinput' % env)
#                 
#         # Rebuild assets
#         run('workon %(virtualenv)s; python manage.py assets build' % env)
#     
#     sudo('/etc/init.d/supervisor start')
    
def metronic_test_update():
    require('path')
    
    run('~/bin/dropbox.py start')
    time.sleep(15)
    run('~/bin/dropbox.py stop')
    with cd(env.path):
        run('cp -ar ~/Dropbox/HTML\ Bag\ of\ Gold/Teste\ in\ Progress/pages/* bagogold/templates/teste')
        run('cp -ar ~/Dropbox/HTML\ Bag\ of\ Gold/Teste\ in\ Progress/assets bagogold/static/')
        
        # Collect static files
        run('source ~/.virtualenvs/bagogold/bin/activate; python manage.py collectstatic --noinput')
        
    sudo('service apache2 reload')
    