from django.db import models
from routes.models import Route


class Vehicle(models.Model):
    """Транспортное средство"""
    route = models.ForeignKey(
        Route,
        on_delete=models.SET_NULL,
        null=True,
        related_name='vehicles',
        verbose_name='Маршрут'
    )
    number_plate = models.CharField(max_length=20, verbose_name='Гос. номер')
    is_active = models.BooleanField(default=True, verbose_name='На линии')

    class Meta:
        verbose_name = 'Транспортное средство'
        verbose_name_plural = 'Транспортные средства'

    def __str__(self):
        return f'{self.number_plate} ({self.route})'


class VehicleLocation(models.Model):
    """Текущая GPS-позиция транспорта"""
    vehicle = models.OneToOneField(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='location',
        verbose_name='Транспорт'
    )
    latitude = models.FloatField(verbose_name='Широта')
    longitude = models.FloatField(verbose_name='Долгота')
    speed = models.FloatField(default=0, verbose_name='Скорость (км/ч)')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Позиция транспорта'
        verbose_name_plural = 'Позиции транспорта'

    def __str__(self):
        return f'{self.vehicle} — ({self.latitude}, {self.longitude})'