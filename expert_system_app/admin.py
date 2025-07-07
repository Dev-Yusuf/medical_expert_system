from django.contrib import admin
from .models import Symptom, Disease, DiseaseSymptom, Treatment, Rule

class DiseaseSymptomInline(admin.TabularInline):
    model = DiseaseSymptom
    extra = 1  # How many extra forms to show

class DiseaseAdmin(admin.ModelAdmin):
    inlines = (DiseaseSymptomInline,)
    list_display = ('name', 'description')

class SymptomAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(Symptom, SymptomAdmin)
admin.site.register(Disease, DiseaseAdmin)
admin.site.register(Treatment)
admin.site.register(Rule)