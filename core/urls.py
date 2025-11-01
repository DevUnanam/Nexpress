from django.urls import path
from .views import (
    HomeView, RegisterView, CreateShipmentView, ShipmentSuccessView,
    TrackShipmentView, TrackFormView, TrackingAPIView, CourierDashboardView,
    ShipmentStatusUpdateView, AdminDashboardView, AdminShipmentListView,
    AdminShipmentUpdateView, ContactView, RecipientDashboardView
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('register/', RegisterView.as_view(), name='register'),
    path('shipment/create/', CreateShipmentView.as_view(), name='create_shipment'),
    path('shipment/success/', ShipmentSuccessView.as_view(), name='shipment_success'),
    path('track/', TrackFormView.as_view(), name='track_form'),
    path('track/<str:tracking_number>/', TrackShipmentView.as_view(), name='track_shipment'),
    path('api/track/<str:tracking_number>/', TrackingAPIView.as_view(), name='api_track_shipment'),
    path('courier/dashboard/', CourierDashboardView.as_view(), name='courier_dashboard'),
    path('recipient/dashboard/', RecipientDashboardView.as_view(), name='recipient_dashboard'),
    path('api/shipment/<str:tracking_number>/update/', ShipmentStatusUpdateView.as_view(), name='shipment_status_update'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('manage/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('manage/shipments/', AdminShipmentListView.as_view(), name='admin_shipment_list'),
    path('manage/shipment/<str:tracking_number>/update/', AdminShipmentUpdateView.as_view(), name='admin_shipment_update'),
]
