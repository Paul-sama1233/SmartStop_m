from django.db import models


class MetroLine(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название линии')
    color = models.CharField(max_length=7, verbose_name='Цвет линии (HEX)', default='#FF0000')
    waypoints = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Промежуточные точки маршрута'
    )

    class Meta:
        verbose_name = 'Линия метро'
        verbose_name_plural = 'Линии метро'

    def __str__(self):
        return self.name


class MetroStation(models.Model):
    line = models.ForeignKey(
        MetroLine,
        on_delete=models.CASCADE,
        related_name='stations',
        verbose_name='Линия'
    )
    name = models.CharField(max_length=100, verbose_name='Название станции')
    latitude = models.FloatField(verbose_name='Широта')
    longitude = models.FloatField(verbose_name='Долгота')
    order = models.PositiveIntegerField(verbose_name='Порядок на линии')
    interval_minutes = models.PositiveIntegerField(
        default=5,
        verbose_name='Интервал движения (мин)'
    )

    class Meta:
        verbose_name = 'Станция метро'
        verbose_name_plural = 'Станции метро'
        ordering = ['order']

    def __str__(self):
        return f'{self.line.name} — {self.name}'