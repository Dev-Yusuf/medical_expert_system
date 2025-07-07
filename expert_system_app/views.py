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

        return render(request, 'expert_system_app/results.html', {'results': results, 'selected_symptoms': Symptom.objects.filter(id__in=selected_symptom_ids)})
    
    return render(request, 'expert_system_app/diagnosis_form.html', {'symptoms': symptoms})

def chatbot_interface(request):
    return render(request, 'expert_system_app/chatbot.html')

def chatbot_query(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')

        if not user_message:
            return JsonResponse({'error': 'Empty message received'}, status=400)

        try:
            # Construct a prompt for the AI model
            system_prompt = (
                "You are a helpful medical assistant for a community health worker. "
                "Your purpose is to provide preliminary suggestions based on symptoms. "
                "You must always include a disclaimer that the user should consult a qualified doctor. "
                "Do not provide a diagnosis that is definitive. Use phrases like 'it could possibly be...' or 'symptoms suggest...'."
                "Keep your responses concise and easy to understand."
            )

            # Call the OpenAI API
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=200,
                temperature=0.7,
            )

            ai_reply = response.choices[0].message.content.strip()
            return JsonResponse({'reply': ai_reply})

        except openai.RateLimitError as e:
            print(f"OpenAI RateLimitError: {e}")
            return JsonResponse({'error': 'The AI service is currently overloaded. Please try again in a few moments.'}, status=429)
        except openai.AuthenticationError as e:
            print(f"OpenAI AuthenticationError: {e}")
            return JsonResponse({'error': 'There is an issue with the AI service configuration. Please contact support.'}, status=500)
        except openai.APIError as e:
            print(f"OpenAI APIError: {e}")
            return JsonResponse({'error': 'An unexpected error occurred with the AI service. Please try again later.'}, status=500)
        except Exception as e:
            # Log the error for debugging
            print(f"Error calling OpenAI API: {e}")
            return JsonResponse({'error': 'Sorry, I am having trouble connecting to the AI service. Please try again later.'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

# Results page view (though diagnosis_form redirects to it, a direct GET might be useful for testing)
def results_page(request):
    # This view is mostly to allow direct navigation if needed, 
    # but results are typically shown via POST from diagnosis_form.
    # You could pass dummy data or a message indicating no results if accessed directly.
    return render(request, 'expert_system_app/results.html', {'results': []}) 