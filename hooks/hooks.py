# -*- coding: utf-8 -*-
from pylint.lint import Run
from django.core.management import call_command

# Chamado no pretxncommit
def rodar_pylint(ui, repo, **kwargs):
    """Roda o pylint nos arquivos .py alterados"""
    print 'rodar pylint'
    changed_files = [os.path.abspath(file) for file in repo[_node].changeset()[3]]
    print changed_files
    
    for change in [changed_file for changed_file in changed_files if '.py' in changed_file]:
        print change
        print Run(['--errors-only', change]) 
        # TODO verificar erros
        
# Chamado no pretxncommit
def testar_para_deploy(ui, repo, **kwargs):
    """Gera testes caso os branches sejam os de produção"""
    branch = BRANCH_CODE
    if branch == 'prod' or branch == 'hotfix':
        print 'rodar testes'
        out = StringIO()

        call_command('test', 'bagogold.bagogold.tests.test_views', interactive=False, keepdb=True, stdout=out)
        value = out.getvalue()
        print value
        return int(value)
        
# Chamado no commit
def rodar_collectstatic(ui, repo, **kwargs):
    branch = BRANCH_CODE
    if branch == 'prod' or branch == 'hotfix':
        print 'rodar testes'
        out = StringIO()

        call_command('collectstatic', interactive=False, stdout=out)
        value = out.getvalue()
        print value
        
# Chamado no commit
# gerar bash com
#commit =
#commit.gerar_build_docker_cron = docker image build -t nizbel/bagofgold:cron -f Dockercron --add-host=database:172.17.0.1 .
#commit.gerar_build_docker_prod = docker image build -t nizbel/bagofgold:prod -f Dockerprod --add-host=database:172.17.0.1 .
#commit.login_docker = docker login --username=$DOCKER_USER --password=$DOCKER_PASS
#commit.docker_push_cron = docker push nizbel/bagofgold:cron
#commit.docker_push_prod = docker push nizbel/bagofgold:prod
#commit.fabfile = fab prod update
