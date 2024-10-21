from django.urls import path
from . import views

urlpatterns = [
    path('upload-faq/', views.upload_faq, name='upload_faq'),
    path('settings/', views.chatbot_settings, name='chatbot_settings'),
]