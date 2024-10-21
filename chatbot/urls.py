from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_interface, name='chatbot_interface'),
    path('api/message/', views.chatbot_message, name='chatbot_message'),
    path('api/settings/', views.get_chatbot_settings, name='chatbot_settings'),
    path('api/reload-faq/', views.reload_faq, name='reload_faq'),
]