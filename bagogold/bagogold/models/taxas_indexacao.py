# -*- coding: utf-8 -*-
from django.db import models

class HistoricoTaxaDI (models.Model):
    data = models.DateField(u'Data')
    taxa = models.DecimalField(u'Rendimento anual', max_digits=5, decimal_places=2, unique_for_date='data')
    
    def save(self, *args, **kw):
        if not HistoricoTaxaDI.objects.filter(taxa=self.taxa, data=self.data).exists():
            super(HistoricoTaxaDI, self).save(*args, **kw)

class HistoricoTaxaSelic (models.Model):
    data = models.DateField(u'Data')
    taxa_diaria = models.DecimalField(u'Taxa diária', max_digits=11, decimal_places=9, unique_for_date='data')
    
    def __unicode__(self):
        return u'%s%% em %s' % (str(self.taxa_diaria), self.data)
    
    def save(self, *args, **kw):
        if not HistoricoTaxaSelic.objects.filter(taxa_diaria=self.taxa_diaria, data=self.data).exists():
            super(HistoricoTaxaSelic, self).save(*args, **kw)