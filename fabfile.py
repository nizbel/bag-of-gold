# -*- encoding: utf-8 -*-
from __future__ import with_statement
from fabric.api import env, require, run, sudo, local as lrun
from fabric.context_managers import cd
from fabric.contrib.files import append, contains, exists
import datetime
import time
from bagogold.bagogold.management.commands.preparar_backup import preparar_backup




# Servers

def prod():
    env.config = 'PROD'
    env.hosts = ['bagofgold.com.br']
    env.path = 'bagogold'
    env.repository = 'https://bitbucket.org/nizbel/bag-of-gold'
    env.user = 'bagofgold'
    env.virtualenv = 'bagogold'
    env.virtualenv_path = '/home/bagofgold/.virtualenvs/bagogold'
    env.forward_agent = True
#     env.procs = ['nginx', 'site', 'winfinity']

def dev():
    env.run = lrun
    env.config = 'DEV'
    env.hosts = ['localhost']
    env.path = 'bagogold'
    env.repository = 'https://bitbucket.org/nizbel/bag-of-gold'
    env.user = 'nizbel'
    env.virtualenv = 'bagogold'
    env.virtualenv_path = '/home/nizbel/.virtualenvs/bagogold'

# Actions

def setup():
    require('path')
    require('repository')
    require('config')
     
    # Setup virtualenv and virtualenvwrapper
    # NOTE: pip must already be installed on the system
    sudo('pip install virtualenv virtualenvwrapper', shell=False)
    if not exists('~/.profile'):
        run('touch ~/.profile')
    if not exists('~/.virtualenvs'):
        run('mkdir ~/.virtualenvs')
    if not contains('WORKON_HOME', '~/.profile'):
        append(('\nexport WORKON_HOME=$HOME/.virtualenvs'
                '\nsource /usr/local/bin/virtualenvwrapper.sh'), '~/.profile')
        run('source ~/.profile')
 
    # Create the virtualenv
    run('mkvirtualenv %(virtualenv)s' % env)
  
    # Clone the repository
    if not exists(env.path):
        run('hg clone %(repository)s %(path)s' % env)

def alterar_cron():
    if env.config == 'PROD':
        run('crontab ~/%s/crontab_prod' % env.path)
    elif env.config == 'DEV':
        run('crontab ~/%s/crontab_copy' % env.path)

def update(requirements=False, rev=None):
    require('path')
    require('virtualenv')
    env.warn_only = True
 
    # Pegar revisão
    rev = rev
    # Se não há revisão, verificar se há update a ser feito
    if not rev:
        branch = verificar_update()
        if not branch:
            return
 
    # Stop apache
    sudo('service apache2 stop', shell=False)
    
    run('workon %(virtualenv)s' % {'virtualenv': env.virtualenv})
    
    # Backup first... always!
    if env.config == 'PROD':
        with cd(env.path):
            run('python manage.py preparar_backup')
        
        # Stop postgres
        sudo('/etc/init.d/postgresql stop', shell=False)
         
    # Update the code
    with cd(env.path):
        run('find . -name "*.pyc" | xargs rm')
        if rev:
            run('hg pull; hg update -r %(rev)s' % {'rev': rev})
        else:
            run('hg pull; hg update %(branch)s' % {'branch': branch})
        # Atualizar requirements
        sudo('pip install -U -r requirements.txt' % env)
 
        # Syncdb, migrate, and sync extensions
        run('python manage.py migrate --noinput')
         
        # Collect static files
        sudo('python manage.py collectstatic --noinput', shell=False)
        
        # Alterar cronjob
        alterar_cron()
    
    if env.config == 'PROD':
        # Start postgres
        sudo('/etc/init.d/postgresql start', shell=False)
    
    # Start apache
    sudo('service apache2 start', shell=False)
    
def verificar_update():
    run('workon %(virtualenv)s' % {'virtualenv': env.virtualenv})
    with cd(env.path):
        run('hg pull', shell=False)
        # Verificar datas dos últimos commits em prod e hotfix
        hotfix_date = run('hg head hotfix --template "{date}"')  
        prod_date = run('hg head prod --template "{date}"')
        hotfix_date = datetime.datetime.fromtimestamp(int(hotfix_date.split('.')[0])) - datetime.timedelta(seconds=int(hotfix_date.split('.')[1]))
        prod_date = datetime.datetime.fromtimestamp(int(prod_date.split('.')[0])) - datetime.timedelta(seconds=int(prod_date.split('.')[1]))
        
        # Buscar data da revisão atual
        atual_date = run('hg parent --template "{date}"')  
        atual_date = datetime.datetime.fromtimestamp(int(atual_date.split('.')[0])) - datetime.timedelta(seconds=int(atual_date.split('.')[1]))
        if max(hotfix_date, prod_date) > atual_date:
            if hotfix_date > prod_date:
                return 'hotfix'
            else:
                return 'prod'
        else:
            return None
            
        
# TODO preparar verificação de update a fazer 
# hg log -b prod --template '{rev}\n' -l 1
