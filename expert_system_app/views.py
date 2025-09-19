from django.shortcuts import render
from django.http import JsonResponse
from .models import Symptom, Disease
import json

# Import the Gemini functions
from .gemini_integration import get_symptoms_from_user_text, generate_friendly_diagnosis_response

def home(request):
    return render(request, 'expert_system_app/home.html')

def diagnosis_form(request):
    # This view remains unchanged
    symptoms = Symptom.objects.all()
    if request.method == 'POST':
        selected_symptom_ids = request.POST.getlist('symptoms')
        if not selected_symptom_ids:
            return render(request, 'expert_system_app/diagnosis_form.html', {
                'symptoms': symptoms, 'error': 'Please select at least one symptom.'
            })
        results = []
        selected_symptom_ids_set = set(map(int, selected_symptom_ids))
        all_diseases = Disease.objects.prefetch_related('diseasesymptom_set', 'treatments').all()
        for disease in all_diseases:
            disease_symptoms = disease.diseasesymptom_set.all()
            if not disease_symptoms:
                continue
            total_possible_score = sum(ds.weight for ds in disease_symptoms)
            patient_score = sum(ds.weight for ds in disease_symptoms if ds.symptom_id in selected_symptom_ids_set)
            if patient_score > 0 and total_possible_score > 0:
                score_percentage = round((patient_score / total_possible_score) * 100)
                results.append({
                    'disease': disease, 'score': score_percentage, 'treatments': disease.treatments.all()
                })
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        return render(request, 'expert_system_app/diagnosis_results.html', {'results': results, 'selected_symptoms': Symptom.objects.filter(id__in=selected_symptom_ids)})
    return render(request, 'expert_system_app/diagnosis_form.html', {'symptoms': symptoms})


def chatbot_interface(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')

            if not user_message:
                return JsonResponse({'reply': 'Please describe your symptoms.'})

            # Get all symptom names from the database (lowercase for matching)
            all_symptoms_db = {s.name.lower(): s.name for s in Symptom.objects.all()}
            
            # Get accurately mapped symptoms from Gemini
            extracted_symptoms_lower = get_symptoms_from_user_text(user_message, list(all_symptoms_db.keys()))

            if not extracted_symptoms_lower:
                return JsonResponse({'reply': "I couldn't identify any known symptoms in your message. Could you please try rephrasing? For example, say 'I have a fever and a headache'."})

            # Convert back to original casing for database query
            original_case_symptoms = [all_symptoms_db[s_lower] for s_lower in extracted_symptoms_lower if s_lower in all_symptoms_db]
            matched_symptoms = Symptom.objects.filter(name__in=original_case_symptoms)
            
            if not matched_symptoms:
                return JsonResponse({'reply': "I was able to identify symptoms, but couldn't match them to a disease. Please contact a doctor."})

            # --- Diagnosis Logic ---
            results = []
            all_diseases = Disease.objects.prefetch_related('diseasesymptom_set').all()
            matched_symptom_ids = {s.id for s in matched_symptoms}

            for disease in all_diseases:
                patient_score = sum(ds.weight for ds in disease.diseasesymptom_set.all() if ds.symptom_id in matched_symptom_ids)
                if patient_score > 0:
                    total_possible_score = sum(ds.weight for ds in disease.diseasesymptom_set.all())
                    if total_possible_score > 0:
                        score_percentage = round((patient_score / total_possible_score) * 100)
                        # --- THE FIX IS HERE: The threshold check has been removed ---
                        results.append({'disease': disease, 'score': score_percentage})
            
            if not results:
                # This should now only be triggered if a symptom is not linked to any disease.
                return JsonResponse({'reply': "Based on your symptoms, I couldn't find a likely match in my database. Please consult a doctor."})

            # Sort to find the most likely disease
            results = sorted(results, key=lambda x: x['score'], reverse=True)
            top_disease = results[0]['disease']

            # Generate the final, friendly response
            bot_response = generate_friendly_diagnosis_response(top_disease, original_case_symptoms)
            
            return JsonResponse({'reply': bot_response})

        except Exception as e:
            print(f"Chatbot Error in View: {e}")
            return JsonResponse({'error': 'An internal error occurred.'}, status=500)

    # Render the chatbot page on a GET request
    return render(request, 'expert_system_app/chatbot_interface.html')