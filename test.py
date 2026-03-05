import google.generativeai as genai

genai.configure(api_key="AIzaSyA5y116werRrYlijOQjLtn8tyUajSXWir0")
model = genai.GenerativeModel("gemini-2.0-flash")
response = model.generate_content("Say hello from RegWatch!")
print(response.text)