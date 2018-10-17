# -*- encoding: utf-8 -*-
from __future__ import with_statement
from bagogold import settings
from fabric.api import env, require, run, sudo, local as lrun
from fabric.context_managers import cd
from fabric.contrib.files import append, contains, exists
import datetime
import re
import time

STATIC_FOLDER = settings.STATICFILES_DIRS[0]
CSS_MET_BASE_FOLDER = STATIC_FOLDER + '/assets/global/css'
CSS_MET_LAYOUT_FOLDER = STATIC_FOLDER + '/assets/layouts/layout3/css'
CSS_MET_ICONS_FOLDER = ''
CSS_JANGO_THEME_FOLDER = STATIC_FOLDER + '/assets_jango/demos/default/css'

IP_MAIN = '18.221.194.175'
IP_SUPPORT = '18.219.213.179'

# 23.253.149.64
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

def prod_ec2():
    env.config = 'PROD_EC2'
    env.hosts = [IP_MAIN] # 18.221.194.175    bagofgold.com.br
#     env.path = 'bagogold'
#     env.repository = 'https://bitbucket.org/nizbel/bag-of-gold'
    env.user = 'ubuntu'
#     env.virtualenv = 'bagogold'
#     env.virtualenv_path = '/home/bagofgold/.virtualenvs/bagogold'
    env.forward_agent = True
#     env.procs = ['nginx', 'site', 'winfinity']
    
def prod_ec2_support():
    env.config = 'PROD_EC2_SUPPORT'
    env.hosts = [IP_SUPPORT]
    env.user = 'ubuntu'
    env.forward_agent = True

def dev():
    env.run = lrun
    env.config = 'DEV'
    env.hosts = ['localhost']
    env.path = 'bagogold'
    env.repository = 'https://bitbucket.org/nizbel/bag-of-gold'
    env.user = 'nizbel'
    env.virtualenv = 'bagogold'
    env.virtualenv_path = '/home/nizbel/.virtualenvs/bagogold'
    env.password = 'nizbaal'
    env.key_filename = '/home/nizbel/.ssh/id_rsa'

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
    elif env.config == 'PROD_EC2_SUPPORT':
        # Verificar se já não existe container com nome teste
        info_container_teste = run('docker container ls -f name=altera_cron')
        if 'altera_cron' in info_container_teste:
            run('docker container stop altera_cron')
            run('docker container rm altera_cron')
        
        run('docker run --add-host=database:172.17.0.1 --name altera_cron -d nizbel/bagofgold:cron')
        try:
            # Copiar arquivo, setar crontab e apagá-lo
            run('docker cp altera_cron:/home/bagofgold/bagogold/crontab_ec2 ~/crontab_ec2')
            run('crontab ~/crontab_ec2')
            run('rm ~/crontab_ec2')
        except Exception as e:
            print e
        # Finalizar container
        run('docker container stop altera_cron')
        run('docker container rm altera_cron')

def gerar_css_def():
    require('config')
    require('path')

    if env.config != 'DEV':
        print u'Comando deve ser usado apenas para DEV'
        return
    
    with cd(env.path):
        run('gulp minify')
            
        # CSS base do Metronic
        texto = ''
        with open(CSS_MET_BASE_FOLDER + '/components-md.min.css', 'r') as arquivo:
            texto += arquivo.read()
        with open(CSS_MET_BASE_FOLDER + '/plugins-md.min.css', 'r') as arquivo:
            texto += arquivo.read()

        with open(CSS_MET_BASE_FOLDER + '/base.min.css', 'w') as arquivo_final:
            arquivo_final.write(texto)
        
        # CSS de layout do Metronic
        texto = ''
        with open(CSS_MET_LAYOUT_FOLDER + '/layout.min.css', 'r') as arquivo:
            texto += arquivo.read()
        with open(CSS_MET_LAYOUT_FOLDER + '/themes/default.min.css', 'r') as arquivo:
            texto += arquivo.read()
        with open(CSS_MET_LAYOUT_FOLDER + '/custom.min.css', 'r') as arquivo:
            texto += arquivo.read()

        with open(CSS_MET_LAYOUT_FOLDER + '/layout-def.min.css', 'w') as arquivo_final:
            arquivo_final.write(texto)
            
        # CSS de tema do Jango
        CSS_JANGO_THEME_FOLDER
        texto = ''
        with open(CSS_JANGO_THEME_FOLDER + '/plugins.min.css', 'r') as arquivo:
            texto += arquivo.read()
        with open(CSS_JANGO_THEME_FOLDER + '/components.min.css', 'r') as arquivo:
            texto += arquivo.read()
        with open(CSS_JANGO_THEME_FOLDER + '/themes/crusta.min.css', 'r') as arquivo:
            texto += arquivo.read()
        with open(CSS_JANGO_THEME_FOLDER + '/custom.min.css', 'r') as arquivo:
            texto += arquivo.read()

        with open(CSS_JANGO_THEME_FOLDER + '/theme-def.min.css', 'w') as arquivo_final:
            arquivo_final.write(texto)

# Deve ser utilizado em
def minificar_html():
    require('path')
    
    with cd(env.path):
        run('python manage.py minificar_html')

def update(requirements=False, rev=None):
    require('path')
    require('virtualenv')
    
    # Apagar cronjobs por enquanto
    run('crontab -r')
    
    # Dar tempo para verificar cronjobs
    time.sleep(5)
    
    # Verificar se há cronjobs rodando
    cron_running = run('pstree -ap `pidof cron`')

    if re.match('cron,\d+$', cron_running) == None:
        print u'Há cronjob rodando, esperar 10 segundos'
        time.sleep(10)
        
        # Se ainda estiver rodando, voltar cronjobs e desistir
        cron_running = run('pstree -ap `pidof cron`')
        if re.match('cron,\d+$', cron_running) == None:
            print u'Update cancelado pois há cronjob ainda executando'
            alterar_cron()
            return
        
    # Pegar revisão
    rev = rev
    # Se não há revisão, verificar se há update a ser feito
    if not rev:
        branch = verificar_update()
 
    # Stop apache
    sudo('service apache2 stop')
    
    run('workon %(virtualenv)s' % {'virtualenv': env.virtualenv})
    
    # Backup first... always!
    if env.config == 'PROD':
        with cd(env.path):
            run('%s/bin/python ~/%s/manage.py preparar_backup' % (env.virtualenv_path, env.path))
        
        # Stop postgres
        sudo('/etc/init.d/postgresql stop')
         
    # Update the code
    with cd(env.path):
        run('workon %(virtualenv)s' % {'virtualenv': env.virtualenv})
        run('find . -name "*.pyc" | xargs rm')
        if rev:
            run('hg pull; hg update -r %(rev)s -C' % {'rev': rev})
        else:
            run('hg update %(branch)s -C' % {'branch': branch})
        # Atualizar requirements
        sudo('pip install -U -r requirements.txt')
 
        
        if env.config == 'PROD':
            # Start postgres
            sudo('/etc/init.d/postgresql start')
            
        # Migrações
        run('python manage.py migrate --noinput')
         
        # Collect static files
        sudo('python manage.py collectstatic --noinput')
    
    # Minificar usa o manage.py porém o cd já ocorre dentro de seu código
    # "Minificar" html
    minificar_html()
    
    # Alterar cronjob
    alterar_cron()
    
    # Start apache
    sudo('service apache2 start', pty=False)

def update_ec2(requirements=False, rev=None):
#     require('path')
#     require('virtualenv')
    require('config')
# 
    if env.config != 'PROD_EC2' and env.config != 'PROD_EC2_SUPPORT':
        print u'Comando deve ser usado apenas para PROD_EC2'
        return
    
    if env.config == 'PROD_EC2_SUPPORT':
        # Apagar cronjobs por enquanto
#         run('crontab -r')
        
        # Dar tempo para verificar cronjobs
        time.sleep(5)
        
        # Verificar se há cronjobs rodando
        cron_running = run('pstree -ap `pidof cron`')
    
        if 'bagofgold' in cron_running:
            print u'Há cronjob rodando, esperar 10 segundos'
            time.sleep(10)
            
            # Se ainda estiver rodando, voltar cronjobs e desistir
            cron_running = run('pstree -ap `pidof cron`')
            if 'bagofgold' in cron_running:
                print u'Update cancelado pois há cronjob ainda executando'
                alterar_cron()
                return
    
    # Pegar revisão
    #rev = rev
    # Se não há revisão, verificar se há update a ser feito
    #if not rev:
    #    branch = verificar_update()
 
    # Stop apache
    #sudo('service apache2 stop')
#     run('docker stack rm bagofgold')
#     run('docker swarm leave --force')    

    #run('workon %(virtualenv)s' % {'virtualenv': env.virtualenv})
    
    if env.config == 'PROD_EC2_SUPPORT':
        # Backup first... always!
        run('docker run --add-host=database:%s nizbel/bagofgold:cron python manage.py preparar_backup' % (IP_MAIN))
        #run('%s/bin/python ~/%s/manage.py preparar_backup' % (env.virtualenv_path, env.path))
      
    # Stop postgres
#     sudo('/etc/init.d/postgresql stop')
         
    # Update the code
    #run('workon %(virtualenv)s' % {'virtualenv': env.virtualenv})
    #run('find . -name "*.pyc" | xargs rm')
    #if rev:
        #run('hg pull; hg update -r %(rev)s -C' % {'rev': rev})
    #else:
        #run('hg update %(branch)s -C' % {'branch': branch})
    # Atualizar requirements
    #sudo('pip install -U -r requirements.txt')
#     run('docker login')
    if env.config == 'PROD_EC2_SUPPORT':
        run('docker pull nizbel/bagofgold:cron')
    elif env.config == 'PROD_EC2':
        run('docker pull nizbel/bagofgold:prod')
        
    # Start postgres
#     sudo('/etc/init.d/postgresql start')
          
    if env.config == 'PROD_EC2_SUPPORT':
        # Migrações
        #run('python manage.py migrate --noinput')
        run('docker run --add-host=database:%s nizbel/bagofgold:cron python manage.py migrate --noinput' % (IP_MAIN))
         
    if env.config == 'PROD_EC2_SUPPORT':
        # Collect static files
        #sudo('python manage.py collectstatic --noinput')
        run('docker run --add-host=database:%s nizbel/bagofgold:cron python manage.py collectstatic --noinput -i admin' % (IP_MAIN))
    
    if env.config == 'PROD_EC2_SUPPORT':
        # Alterar cronjob
        alterar_cron()
    
    # Start apache
    #sudo('service apache2 start', pty=False)
#     run('docker swarm init')
    if env.config == 'PROD_EC2':
        run('docker stack deploy -c docker-compose.yml --with-registry-auth bagofgold')
    
    # Apagar imagens nao utilizadas mais
    run('docker image prune -f')
    
def reset_pg():
    require('config')
    
    if env.config == 'PROD':
        sudo('/etc/init.d/postgresql stop')
        sudo('/etc/init.d/postgresql start')
        
    elif env.config == 'PROD_EC2':
        sudo('/etc/init.d/postgresql stop')
        sudo('/etc/init.d/postgresql start')
    
def verificar_cron():
    require('path')
    
    run('pstree -ap `pidof cron`')
    
def verificar_update():
    run('workon %(virtualenv)s' % {'virtualenv': env.virtualenv})
    with cd(env.path):
        run('hg pull', shell=False)
        # Verificar datas dos últimos commits em prod e hotfix
        hotfix_date = run('hg head hotfix --template "{date}"')  
        prod_date = run('hg head prod --template "{date}"')
        hotfix_date = datetime.datetime.fromtimestamp(int(hotfix_date.split('.')[0])) - datetime.timedelta(seconds=int(hotfix_date.split('.')[1]))
        prod_date = datetime.datetime.fromtimestamp(int(prod_date.split('.')[0])) - datetime.timedelta(seconds=int(prod_date.split('.')[1]))
        
        if hotfix_date > prod_date:
            return 'hotfix'
        else:
            return 'prod'
