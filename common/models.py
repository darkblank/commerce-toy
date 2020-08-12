from django.contrib.gis.db import models


class UpdatedAtModel(models.Model):
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CreatedAtModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class TimeStampModel(CreatedAtModel, UpdatedAtModel):
    class Meta:
        abstract = True
