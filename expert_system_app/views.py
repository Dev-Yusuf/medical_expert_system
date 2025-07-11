from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from .models import Symptom, Disease, Rule, Treatment, DiseaseSymptom
import json
import openai

# Set the OpenAI API key
openai.api_key = settings.OPENAI_API_KEY

# Create your views here.
def home(request):
    return render(request, 'expert_system_app/home.html')

def diagnosis_form(request):
    symptoms = Symptom.objects.all()
    if request.method == 'POST':
        selected_symptom_ids = request.POST.getlist('symptoms')
        # Basic inference engine logic (placeholder)
        if not selected_symptom_ids:
            # Handle case with no symptoms selected if necessary
            return render(request, 'expert_system_app/diagnosis_form.html', {
                'symptoms': symptoms,
                'error': 'Please select at least one symptom.'
            })

        # --- New Weighted Inference Engine Logic ---
        results = []
        selected_symptom_ids_set = set(map(int, selected_symptom_ids))

        # Get all diseases and prefetch their related symptoms and treatments
        all_diseases = Disease.objects.prefetch_related('diseasesymptom_set', 'treatments').all()

        for disease in all_diseases:
            disease_symptoms = disease.diseasesymptom_set.all()
            
            if not disease_symptoms:
                continue

            total_possible_score = sum(ds.weight for ds in disease_symptoms)
            patient_score = 0

            for ds in disease_symptoms:
                if ds.symptom_id in selected_symptom_ids_set:
                    patient_score += ds.weight
            
            if patient_score > 0 and total_possible_score > 0:
                # Calculate percentage score
                score_percentage = round((patient_score / total_possible_score) * 100)
                
                results.append({
                    'disease': disease,
                    'score': score_percentage,
                    'treatments': disease.treatments.all()
                })

        # Sort results by the new weighted score
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        # --- Inference Engine Logic End ---

        return render(request, 'expert_system_app/diagnosis_results.html', {'results': results, 'selected_symptoms': Symptom.objects.filter(id__in=selected_symptom_ids)})
    
    return render(request, 'expert_system_app/diagnosis_form.html', {'symptoms': symptoms})

def chatbot_interface(request):
    return render(request, 'expert_system_app/chatbot_interface.html')

def chatbot_query(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').lower()

            if not user_message:
                return JsonResponse({'reply': 'Please describe your symptoms.'})

            # --- Rule-Based Inference Engine for Chatbot ---
            all_symptoms = Symptom.objects.all()
            matched_symptom_ids = set()

            # --- Intelligent Symptom Identification ---
            # Define common English stop words to ignore
            stop_words = set(['i', 'a', 'about', 'an', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'how', 'in', 'is', 'it', 'of', 'on', 'or', 'that', 'the', 'this', 'to', 'was', 'what', 'when', 'where', 'who', 'will', 'with', 'have', 'feel', 'feeling', 'and'])
            
            # Clean user's message by removing punctuation and stop words
            user_message_cleaned = ''.join(c for c in user_message if c.isalnum() or c.isspace())
            user_words = set(user_message_cleaned.split()) - stop_words

            # Find matching symptoms
            for symptom in all_symptoms:
                symptom_words = set(symptom.name.lower().split())
                # Check for a direct match of the symptom name or intersection of important words
                if symptom.name.lower() in user_message or symptom_words.intersection(user_words):
                    matched_symptom_ids.add(symptom.id)

            if not matched_symptom_ids:
                return JsonResponse({'reply': "I couldn't identify any known symptoms in your message. Could you please describe them differently? Remember to use specific terms like 'fever', 'cough', or 'headache'."})

            # Run the same weighted scoring logic as the main form
            results = []
            all_diseases = Disease.objects.prefetch_related('diseasesymptom_set').all()

            for disease in all_diseases:
                disease_symptoms = disease.diseasesymptom_set.all()
                if not disease_symptoms:
                    continue

                total_possible_score = sum(ds.weight for ds in disease_symptoms)
                patient_score = sum(ds.weight for ds in disease_symptoms if ds.symptom_id in matched_symptom_ids)

                if patient_score > 0 and total_possible_score > 0:
                    score_percentage = round((patient_score / total_possible_score) * 100)
                    if score_percentage > 20: # Set a threshold to avoid irrelevant results
                        results.append({'disease_name': disease.name, 'score': score_percentage})
            
            # Sort results to find the most likely candidates
            results = sorted(results, key=lambda x: x['score'], reverse=True)

            # --- Generate a Dynamic Response ---
            if not results:
                response_text = "Based on the symptoms you've described, I couldn't find a likely match in my database. It's always best to consult a doctor for an accurate diagnosis."
            else:
                top_results = results[:2] # Get top 2 results
                disease_names = [res['disease_name'] for res in top_results]
                
                if len(disease_names) > 1:
                    response_text = f"The symptoms you mentioned could suggest a few possibilities, such as {disease_names[0]} or {disease_names[1]}."
                else:
                    response_text = f"The symptoms you mentioned could suggest a possibility of {disease_names[0]}."
                
                response_text += "\n\nHowever, this is just a preliminary suggestion based on the information provided. It is not a diagnosis. Please consult a qualified medical professional for an accurate assessment."

            return JsonResponse({'reply': response_text})

        except Exception as e:
            print(f"Chatbot Error: {e}")
            return JsonResponse({'error': 'An internal error occurred. Please try again later.'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)
