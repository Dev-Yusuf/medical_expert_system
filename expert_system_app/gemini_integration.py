import google.generativeai as genai
from django.conf import settings
import re

if not settings.GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in settings. Please check your .env file and settings.py.")

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_symptoms_from_user_text(user_input, all_symptoms_list_lower):
    """
    Maps user expression to a predefined list of symptoms (case-insensitive).
    """
    symptom_list_for_prompt = "\n".join([f"- {symptom}" for symptom in all_symptoms_list_lower])

    prompt = f"""
    You are an AI medical terminologist. Your only job is to read a user's message and map their words to a specific list of symptoms. The list is already in lowercase.

    **Official Symptom List (lowercase):**
    ---
    {symptom_list_for_prompt}
    ---

    **User's Message:** "{user_input}"

    **Task:**
    Return a comma-separated list of the exact symptom names from the Official Symptom List that match the user's message. Ensure your output is also in lowercase.
    """
    try:
        response = model.generate_content(prompt)
        
        cleaned_text = response.text.strip().lower() # Convert entire response to lowercase
        
        # Match only symptoms that are in our official list
        symptoms = [symptom.strip() for symptom in cleaned_text.split(',') if symptom.strip() in all_symptoms_list_lower]
        
        print(f"--- Gemini Raw Response (lower): '{cleaned_text}'")
        print(f"--- Parsed Symptoms (lower): {symptoms}")
        return symptoms

    except Exception as e:
        print(f"ERROR DURING GEMINI CALL: {e}")
        return []

def generate_friendly_diagnosis_response(diagnosis, symptoms):
    """
    Generates a user-friendly explanation of a diagnosis.
    """
    symptoms_text = ", ".join(symptoms)
    prompt = f"""
    You are an empathetic AI medical assistant. A rule-based system suggested a possible diagnosis of '{diagnosis.name}' based on these symptoms: {symptoms_text}.

    Explain what {diagnosis.name} is in simple, reassuring terms.

    IMPORTANT: You must end your response with this exact disclaimer:
    "Disclaimer: I am an AI assistant and not a medical professional. This is not a real diagnosis. Please consult with a doctor for any health concerns."
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating friendly response: {e}")
        return "I'm sorry, I'm having trouble generating a response right now."                 