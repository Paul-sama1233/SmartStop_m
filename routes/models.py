from django.db import models


class Route(models.Model):
    DIRECTION_CHOICES = [
        ('A-B', 'Прямое направление'),
        ('B-A', 'Обратное направление'),
    ]

    external_id = models.IntegerField(unique=True, verbose_name='ID из opendata')
    number = models.CharField(max_length=10, verbose_name='Номер маршрута')
    name = models.CharField(max_length=255, verbose_name='Название маршрута')
    transport_type = models.CharField(max_length=50, null=True, blank=True, verbose_name='Тип транспорта')
    direction = models.CharField(max_length=5, choices=DIRECTION_CHOICES, default='A-B', verbose_name='Направление')
    length_km = models.FloatField(null=True, blank=True, verbose_name='Длина (км)')
    garage = models.CharField(max_length=255, null=True, blank=True, verbose_name='Автопарк')
    coordinates = models.JSONField(default=list, verbose_name='Координаты')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    vehicle_count = models.PositiveIntegerField(default=0, verbose_name='Количество транспорта')
    work_start = models.TimeField(null=True, blank=True, verbose_name='Начало работы')
    work_end = models.TimeField(null=True, blank=True, verbose_name='Конец работы')
    avg_trip_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name='Среднее время рейса (мин)')
    bus_brand = models.CharField(max_length=100, null=True, blank=True, verbose_name='Марка автобуса')
    is_favorite = models.BooleanField(default=False, verbose_name='Избранный')

    class Meta:
        verbose_name = 'Маршрут'
        verbose_name_plural = 'Маршруты'

    def __str__(self):
        return f'{self.number} ({self.direction}) — {self.name}'


class Stop(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название остановки')
    latitude = models.FloatField(verbose_name='Широта')
    longitude = models.FloatField(verbose_name='Долгота')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        verbose_name = 'Остановка'
        verbose_name_plural = 'Остановки'

    def __str__(self):
        return self.name


class RouteStop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='route_stops', verbose_name='Маршрут')
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='route_stops', verbose_name='Остановка')
    order = models.PositiveIntegerField(verbose_name='Порядок')
    estimated_time = models.PositiveIntegerField(default=0, verbose_name='Время от начала (мин)')

    class Meta:
        verbose_name = 'Остановка маршрута'
        verbose_name_plural = 'Остановки маршрута'
        ordering = ['order']

    def __str__(self):
        return f'{self.route.number} → {self.stop.name}'