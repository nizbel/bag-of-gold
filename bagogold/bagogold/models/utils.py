# -*- coding: utf-8 -*-
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
 
class FuncionalidadeConstrucao (models.Model):
    percentual = models.PositiveSmallIntegerField(u'Percentual feito', validators=[MinValueValidator(0), MaxValueValidator(99)]) 
    tag = models.CharField(u'Tag da funcionalidade', max_length=30)
    
    def __unicode__(self):
        return u'%s (%s%% pronto)' % (self.tag, self.percentual)
