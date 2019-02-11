# -*- coding: utf-8 -*-
import subprocess

from django.core.mail import mail_admins
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Notifica containers que finalizaram com código diferente de 0 e os apaga'

    def handle(self, *args, **options):
        enviar_email_containers_erro(verificar_containers_erro())
        
        
def verificar_containers_erro():
    """Retorna containers que tenham finalizado com código diferente de 0"""
    # Busca containers terminados
    proc_containers_terminados = subprocess.Popen(['docker', 'container', 'ps', '-f', 'status=exited', '-q'], stdout=subprocess.PIPE)
    containers_terminados, _ = proc_containers_terminados.communicate()
    containers_terminados = containers_terminados.split('\n')
    
    proc_containers_terminados_ok = subprocess.Popen(['docker', 'container', 'ps', '-a', '-f', 'exited=0', '-q'], stdout=subprocess.PIPE)
    containers_terminados_ok, _ = proc_containers_terminados_ok.communicate()
    containers_terminados_ok = containers_terminados_ok.split('\n')
    
    containers = [container for container in containers_terminados if container not in containers_terminados_ok]

    return containers
    
def enviar_email_containers_erro(containers):
    for container in containers:
        proc_log = subprocess.Popen(['docker', 'container', 'logs', '--details', container], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log = '\n\n'.join([resultado for resultado in proc_log.communicate() if resultado])
        proc_dados = subprocess.Popen(['docker', 'container', 'inspect', container], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        dados = '\n\n'.join([resultado for resultado in proc_dados.communicate() if resultado])
        
        mail_admins('Erro no container %s' % (container), 'Dados:\n%s\n\n\n\n\nLog:\n%s' % (dados, log))
         
        subprocess.call(['docker', 'container', 'rm', container]) 