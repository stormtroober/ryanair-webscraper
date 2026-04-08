from django.contrib import admin
from .models import Route, PriceRecord


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('origin', 'destination', 'date', 'is_active')
    list_filter = ('is_active',)
    list_editable = ('is_active',)


@admin.register(PriceRecord)
class PriceRecordAdmin(admin.ModelAdmin):
    list_display = ('route', 'amount', 'currency', 'scraped_at')
    list_filter = ('route',)
    readonly_fields = ('scraped_at',)
