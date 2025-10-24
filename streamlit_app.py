import streamlit as st
import pandas as pd
import os
from PIL import Image
import pytesseract

# Hide Streamlit default menu and GitHub links
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)
# TITLE
# ---------------------------------------------------------
st.title(":weight_lifting_man: Get Set, Go!!!")
st.subheader("Performance Driven Personalized Fuelling Requirements and Macro Tracker")

# ---------------------------------------------------------
# CORE LOGIC — FUELING REQUIREMENTS
# ---------------------------------------------------------
def fueling_requirements(intensity: str, weight_kg: float, duration_hr: float, gender: str, goal: str, menstrual_phase=None):
    intensity_carbs = {
        "Low": (3, 5),
        "Moderate": (5, 7),
        "High": (6, 10),
        "Extreme": (8, 12)
    }
    carb_min, carb_max = intensity_carbs.get(intensity, (5, 7))

    if goal == "Weight Loss / Body Composition":
        carb_min *= 0.9
        carb_max *= 0.9

    if gender == "Female" and menstrual_phase:
        if menstrual_phase == "Follicular":
            carb_min *= 1.05
        elif menstrual_phase == "Luteal":
            carb_min *= 0.95
            carb_max *= 0.95

    carbs_min = weight_kg * carb_min
    carbs_max = weight_kg * carb_max

    # Protein
    if intensity in ["High", "Extreme"]:
        protein_min, protein_max = (1.4, 1.8)
    elif intensity == "Low":
        protein_min, protein_max = (1.2, 1.6)
    else:
        protein_min, protein_max = (1.6, 2.2)

    if gender == "Female":
        protein_max = max(protein_max - 0.2, protein_min)

    protein_min_g = weight_kg * protein_min
    protein_max_g = weight_kg * protein_max

    # Fat
    fat_min_g = weight_kg * 0.8
    fat_max_g = weight_kg * 1.0

    # Fluids & sodium
    fluid_loss_ml = 600 * duration_hr
    fluid_replacement_ml = fluid_loss_ml * 1.5
    sodium_mg = 500 * duration_hr

    return {
        "carbs_g_range": (round(carbs_min), round(carbs_max)),
        "protein_g_range": (round(protein_min_g), round(protein_max_g)),
        "fat_g_range": (round(fat_min_g), round(fat_max_g)),
        "fluid_loss_ml": round(fluid_loss_ml),
        "fluid_replacement_ml": round(fluid_replacement_ml),
        "sodium_mg": round(sodium_mg)
    }

# ---------------------------------------------------------
# MICRONUTRIENT RECOMMENDATIONS
# ---------------------------------------------------------
def micronutrient_needs(gender: str, menstrual_phase=None):
    if gender == "Male":
        iron = 8
        calcium = 1000
        vitamin_d = 15
        magnesium = 400
        potassium = 3400
    else:
        iron = 18
        calcium = 1000
        vitamin_d = 15
        magnesium = 320
        potassium = 2600
        if menstrual_phase == "Menstrual":
            iron += 4

    foods = """
**Micronutrient-Rich Foods:**
- **Iron:** Lentils, spinach, red meat, tofu
- **Calcium:** Dairy, fortified plant milk, sesame seeds
- **Vitamin D:** Sunlight, fatty fish, fortified foods
- **Magnesium:** Nuts, whole grains, dark chocolate
- **Potassium:** Bananas, potatoes, leafy greens
"""
    return {
        "Iron (mg)": iron,
        "Calcium (mg)": calcium,
        "Vitamin D (µg)": vitamin_d,
        "Magnesium (mg)": magnesium,
        "Potassium (mg)": potassium,
        "Food Tips": foods
    }

# ---------------------------------------------------------
# FOOD SUGGESTIONS
# ---------------------------------------------------------
def suggest_foods(deficit_protein, deficit_carbs, deficit_fat, diet):
    foods = {
        "Non-Vegetarian": "- Chicken breast (100g) → 22g protein\n- Sweet potato (150g) → 30g carbs\n- Olive oil (1 tbsp) → 14g fat",
        "Vegetarian": "- Paneer (100g) → 22g protein\n- Whole wheat roti (2 pcs) → 40g carbs\n- Olive oil (1 tbsp) → 14g fat",
        "Vegan": "- Tofu (150g) → 20g protein\n- Oats (60g) → 40g carbs\n- Avocado (100g) → 15g fat"
    }

    if deficit_protein <= 0 and deficit_carbs <= 0 and deficit_fat <= 0:
        return "✅ You've met all your macro requirements!"

    return f"""
You still need:
- Protein: {deficit_protein} g
- Carbohydrates: {deficit_carbs} g
- Fat: {deficit_fat} g

Suggested foods ({diet}):
{foods[diet]}
"""

# ---------------------------------------------------------
# OCR EXTRACTION
# ---------------------------------------------------------
def extract_macros_from_image(image):
    try:
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        return f"Error reading image: {e}"

# ---------------------------------------------------------
# UI FLOW
# ---------------------------------------------------------
st.markdown("---")
st.header("Step 1: Workout & Personal Details")

sport = st.selectbox("Select your sport", ["Swimming", "Running", "Cycling", "Gym/Strength Training", "Triathlon"])
intensity = st.selectbox("Select intensity", ["Low", "Moderate", "High", "Extreme"])
weight = st.number_input("Enter your weight (kg)", min_value=30.0, max_value=150.0, value=70.0, step=0.5)
gender = st.radio("Select gender", ["Male", "Female"])
duration = st.number_input("Workout duration (hours)", min_value=0.5, max_value=8.0, value=1.5, step=0.5)
goal = st.radio("Select goal", ["Performance", "Weight Loss / Body Composition"])
diet_choice = st.radio("Select diet type", ["Non-Vegetarian", "Vegetarian", "Vegan"])

menstrual_phase = None
if gender == "Female":
    include_cycle = st.radio("Would you like to include menstrual cycle data?", ["No", "Yes"])
    if include_cycle == "Yes":
        st.info("This helps personalize fueling based on your cycle phase. (Informational only — consult professionals for specifics.)")
        menstrual_phase = st.selectbox("Select your current phase", ["Follicular", "Luteal", "Menstrual", "Ovulatory"])

st.markdown("---")

st.subheader("Step 2: Current Macro Intake")

uploaded_file = st.file_uploader("Upload a food label image (optional)", type=["jpg", "jpeg", "png"])

# Reset session state when a new file is uploaded
if uploaded_file is not None:
    st.session_state.ocr_carbs = 0
    st.session_state.ocr_protein = 0
    st.session_state.ocr_fat = 0

    try:
        from PIL import Image
        import pytesseract
        import re

        image = Image.open(uploaded_file)
        text = pytesseract.image_to_string(image)
        clean_text = text.replace("\n", " ").replace(":", " ").replace("-", " ")
        clean_text = re.sub(r"\s+", " ", clean_text).lower()

        
        # Broader regex for Indian-style labels
        carb_match = re.search(r"(carb|cho|carbohydrates?)\D*?(\d+\.?\d*)", clean_text)
        protein_match = re.search(r"(protein)\D*?(\d+\.?\d*)", clean_text)
        fat_match = re.search(r"(fat|total fat)\D*?(\d+\.?\d*)", clean_text)

        extracted = False
        if carb_match:
            st.session_state.ocr_carbs = float(carb_match.group(2))
            extracted = True
        if protein_match:
            st.session_state.ocr_protein = float(protein_match.group(2))
            extracted = True
        if fat_match:
            st.session_state.ocr_fat = float(fat_match.group(2))
            extracted = True

        if extracted:
            st.success("✅ Nutrition details extracted successfully!")
            st.write("Extracted values (you can edit below):")
            st.write(f"- Carbohydrates: {st.session_state.ocr_carbs} g")
            st.write(f"- Protein: {st.session_state.ocr_protein} g")
            st.write(f"- Fat: {st.session_state.ocr_fat} g")
        else:
            st.warning("⚠️ No clear nutrition info detected. Please check the label text or enter manually.")
            st.info("Tip: Make sure the label includes words like ‘carb’, ‘protein’, or ‘fat’.")

    except Exception as e:
        st.error(f"❌ Error reading image: {e}")

# Auto-fill with extracted values (editable)
intake_carbs = st.number_input("Carbohydrates consumed (g)", min_value=0.0, value=st.session_state.get("ocr_carbs", 0.0), step=5.0)
intake_protein = st.number_input("Protein consumed (g)", min_value=0.0, value=st.session_state.get("ocr_protein", 0.0), step=5.0)
intake_fat = st.number_input("Fat consumed (g)", min_value=0.0, value=st.session_state.get("ocr_fat", 0.0), step=1.0)




st.markdown("---")
if st.button("Calculate Fueling Requirements"):
    results = fueling_requirements(intensity, weight, duration, gender, goal, menstrual_phase)
    micro = micronutrient_needs(gender, menstrual_phase)

    st.subheader("Step 3: Your Daily Fueling Requirements")
    st.write(f"Carbohydrates: {results['carbs_g_range'][0]}–{results['carbs_g_range'][1]} g")
    st.write(f"Protein: {results['protein_g_range'][0]}–{results['protein_g_range'][1]} g")
    st.write(f"Fat: {results['fat_g_range'][0]}–{results['fat_g_range'][1]} g")
    st.write(f"Fluids lost: {results['fluid_loss_ml']} ml → Replace with ~{results['fluid_replacement_ml']} ml")
    st.write(f"Sodium: {results['sodium_mg']} mg")

    st.subheader("Step 4: Macro Deficit")
    deficit_carbs = max(results["carbs_g_range"][0] - intake_carbs, 0)
    deficit_protein = max(results["protein_g_range"][0] - intake_protein, 0)
    deficit_fat = max(results["fat_g_range"][0] - intake_fat, 0)
    st.write(f"Protein deficit: {deficit_protein} g")
    st.write(f"Carbohydrate deficit: {deficit_carbs} g")
    st.write(f"Fat deficit: {deficit_fat} g")

    st.subheader("Step 5: Suggested Foods")
    st.markdown(suggest_foods(deficit_protein, deficit_carbs, deficit_fat, diet_choice))

    st.subheader("Step 6: Micronutrient Recommendations")
    st.write(f"Iron: {micro['Iron (mg)']} mg")
    st.write(f"Calcium: {micro['Calcium (mg)']} mg")
    st.write(f"Vitamin D: {micro['Vitamin D (µg)']} µg")
    st.write(f"Magnesium: {micro['Magnesium (mg)']} mg")
    st.write(f"Potassium: {micro['Potassium (mg)']} mg")
    st.markdown(micro["Food Tips"])
