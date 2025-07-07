from django.db import models

# Create your models here.

class Symptom(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Disease(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    symptoms = models.ManyToManyField(Symptom, through='DiseaseSymptom', related_name='diseases')

    def __str__(self):
        return self.name

class DiseaseSymptom(models.Model):
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE)
    symptom = models.ForeignKey(Symptom, on_delete=models.CASCADE)
    weight = models.IntegerField(default=1, help_text="The importance of the symptom for this disease (e.g., 1-10).")

    class Meta:
        unique_together = ('disease', 'symptom')

    def __str__(self):
        return f'{self.disease.name} - {self.symptom.name}'

class Treatment(models.Model):
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='treatments')
    description = models.TextField()

    def __str__(self):
        return f"Treatment for {self.disease.name}"

class Rule(models.Model):
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='rules')
    symptoms = models.ManyToManyField(Symptom)

    def __str__(self):
        symptom_names = ", ".join([s.name for s in self.symptoms.all()])
        if not symptom_names:
            symptom_names = "No symptoms defined"
        return f"Rule for {self.disease.name} (Symptoms: {symptom_names})"
