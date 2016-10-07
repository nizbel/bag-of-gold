#!/bin/sh

/usr/bin/pg_dump --host localhost --port 5432 --username "bagogold" --no-password  --format custom --blobs --encoding UTF8 --verbose --file "/home/bagofgold/bagogold/backups/backup-$(date +\%H-\%d-\%m-\%Y)" --table "public.auth_group" --table "public.auth_group_permissions" --table "public.auth_permission" --table "public.auth_user" --table "public.auth_user_groups" --table "public.auth_user_user_permissions" --table "public.bagogold_acao" --table "public.bagogold_acaoprovento" --table "public.bagogold_cdb_rdb" --table "public.bagogold_divisao" --table "public.bagogold_divisaooperacaoacao" --table "public.bagogold_divisaooperacaocdb_rdb" --table "public.bagogold_divisaooperacaofii" --table "public.bagogold_divisaooperacaofundoinvestimento" --table "public.bagogold_divisaooperacaolc" --table "public.bagogold_divisaooperacaotd" --table "public.bagogold_divisaoprincipal" --table "public.bagogold_empresa" --table "public.bagogold_fii" --table "public.bagogold_fundoinvestimento" --table "public.bagogold_historicoacao" --table "public.bagogold_historicocarenciacdb_rdb" --table "public.bagogold_historicocarenciafundoinvestimento" --table "public.bagogold_historicocarencialetracredito" --table "public.bagogold_historicofii" --table "public.bagogold_historicoipca" --table "public.bagogold_historicoporcentagemcdb_rdb" --table "public.bagogold_historicoporcentagemletracredito" --table "public.bagogold_historicotaxadi" --table "public.bagogold_historicotitulo" --table "public.bagogold_historicovalorcotas" --table "public.bagogold_historicovalorminimoinvestimento" --table "public.bagogold_historicovalorminimoinvestimentocdb_rdb" --table "public.bagogold_historicovalorminimoinvestimentofundoinvestimento" --table "public.bagogold_investidor" --table "public.bagogold_letracredito" --table "public.bagogold_operacaoacao" --table "public.bagogold_operacaocdb_rdb" --table "public.bagogold_operacaocompravenda" --table "public.bagogold_operacaofii" --table "public.bagogold_operacaofundoinvestimento" --table "public.bagogold_operacaoletracredito" --table "public.bagogold_operacaotitulo" --table "public.bagogold_operacaovendacdb_rdb" --table "public.bagogold_operacaovendaletracredito" --table "public.bagogold_provento" --table "public.bagogold_proventofii" --table "public.bagogold_taxacustodiaacao" --table "public.bagogold_titulo" --table "public.bagogold_transferenciaentredivisoes" --table "public.bagogold_usoproventosoperacaoacao" --table "public.bagogold_usoproventosoperacaofii" --table "public.django_admin_log" --table "public.django_content_type" --table "public.django_migrations" --table "public.django_session" "bagogold"
