from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('route/<int:pk>/', views.route_detail, name='route_detail'),
    path('route/<int:pk>/toggle/', views.route_toggle, name='route_toggle'),
    path('route/<int:pk>/delete/', views.route_delete, name='route_delete'),
    path('route/add/', views.route_add, name='route_add'),
    path('api/prices/<int:pk>/', views.api_prices, name='api_prices'),
    path('api/scrape/', views.scrape_now, name='scrape_now'),
    path('api/logs/', views.log_stream, name='log_stream'),
    path('api/vpn/', views.vpn_toggle, name='vpn_toggle'),
    path('api/status/', views.api_status, name='api_status'),
]
