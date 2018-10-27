"""
Django settings for bagogold project.

Generated by 'django-admin startproject' using Django 1.8.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ALLOWED_HOSTS = ['bagofgold.com.br']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
#     'yahoo_finance',
    'storages',
    
    #Bag-O-Gold
    'bagogold.bagogold',
    'bagogold.pendencias',
    'bagogold.blog',
    'bagogold.cdb_rdb',
    'bagogold.cri_cra',
    'bagogold.fii',
    'bagogold.fundo_investimento',
    'bagogold.criptomoeda',
    'bagogold.lci_lca',
    'bagogold.outros_investimentos',
    'bagogold.lc',
    'bagogold.tesouro_direto',
    'bagogold.debentures',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'bagogold.bagogold.middleware.ultimo_acesso.UltimoAcessoMiddleWare',
)

ROOT_URLCONF = 'bagogold.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_ROOT, 'templates'),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'bagogold.bagogold.context_processors.current_version',
                'bagogold.bagogold.context_processors.env',
                'bagogold.bagogold.context_processors.pendencias_investidor',
            ],
        },
    },
]

WSGI_APPLICATION = 'bagogold.wsgi.application'

LOGIN_REDIRECT_URL = 'inicio:painel_geral'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.INFO: 'alert',
    messages.SUCCESS: 'success bg-green-steel bg-font-green-steel',
    messages.ERROR: 'error bg-red-thunderbird bg-font-red-thunderbird',
}

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_L10N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = True

LOGIN_URL= '/login/'

# Testes
TEST_RUNNER = 'bagogold.bagogold.tests.runner.TimeLoggingTestRunner'

# Configuracoes extras
from conf.conf import *

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR + '/bagogold', "static"),
]

MEDIA_ROOT = 'media/'

# Caminho para arquivos de fundos de investimento
CAMINHO_FUNDO_INVESTIMENTO = MEDIA_ROOT + 'fundo investimento/'
CAMINHO_FUNDO_INVESTIMENTO_CADASTRO = CAMINHO_FUNDO_INVESTIMENTO + 'cadastro/' 
CAMINHO_FUNDO_INVESTIMENTO_HISTORICO = CAMINHO_FUNDO_INVESTIMENTO + 'historico/' 

# Caminho para arquivos de historico recente acoes/fiis
CAMINHO_HISTORICO_RECENTE_ACOES_FIIS = MEDIA_ROOT + 'historico recente/'

# Caminho para arquivos de proventos
CAMINHO_DOCUMENTO_PROVENTOS = MEDIA_ROOT + 'doc proventos/'

# Caminho para backups
CAMINHO_BACKUPS = BASE_DIR + '/backups'

# Configurar precisao de decimais
from decimal import getcontext
getcontext().prec = 18

# Buscar configuracoes adicionais
from conf.settings_local import *