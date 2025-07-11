from django.urls import path
from . import views

app_name = 'expert_system_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('diagnosis/', views.diagnosis_form, name='diagnosis_form'),
    path('chatbot/', views.chatbot_interface, name='chatbot_interface'),
    path('chatbot/query/', views.chatbot_query, name='chatbot_query'),
] 