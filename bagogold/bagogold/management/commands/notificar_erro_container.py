def verificar_containers_erro():
    """Retorna containers que tenham finalizado com código diferente de 0"""
    # Busca containers terminados
    containers_terminados = subprocess.call(['docker', 'container', 'ps', '-f', 'status=exited', '-q'])
    
    containers_terminados_ok = subprocess.call(['docker', 'container', 'ps', '-a', '-f', 'exited=0', '-q'])
    
    containers = [container for container in containers_terminados if container not in containers_terminados_ok]
    
    return containers
    
def enviar_email_containers_erro(containers):
    for container in containers:
        log = subprocess.call(['docker', 'container', '--details', 'logs', container])
        dados = subprocess.call(['docker', 'container', 'inspect', container])
    
        mail_admins('Erro no container %s' % (container), 'Dados:\n%s\n\n\n\n\nLog:\n%s' % (dados, log))
        
        # docker container rm 