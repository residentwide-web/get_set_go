import streamlit as st
import pandas as pd
import os

# Hide Streamlit default menu and GitHub links
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# ------------------------
# Fueling Calculator Logic
# ------------------------
def fueling_requirements(intensity: str, weight_kg: float, duration_hr: float, gender: str, goal: str):
    # Carb multipliers by intensity
    intensity_carbs = {
        "Low": (3, 5),
        "Moderate": (5, 7),
        "High": (6, 10),
        "Extreme": (8, 12)
    }

    if intensity in intensity_carbs:
        carb_min, carb_max = intensity_carbs[intensity]
    else:
        carb_min, carb_max = (5, 7)  # default

    if goal == "Weight Loss / Body Composition":
        carb_min *= 0.9
        carb_max *= 0.9

    carbs_min = weight_kg * carb_min
    carbs_max = weight_kg * carb_max

    # Protein requirements based on intensity
    if intensity in ["High", "Extreme"]:
        protein_min, protein_max = (1.4, 1.8)
    elif intensity == "Low":
        protein_min, protein_max = (1.2, 1.6)
    else:  # Moderate
        protein_min, protein_max = (1.6, 2.2)

    if gender == "Female":
        protein_max = max(protein_max - 0.2, protein_min)

    protein_min_g = weight_kg * protein_min
    protein_max_g = weight_kg * protein_max

    # Fat requirement (0.8–1.0 g/kg)
    fat_min_g = weight_kg * 0.8
    fat_max_g = weight_kg * 1.0

    # Fluids and sodium
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

# ------------------------
# Food Suggestions
# ------------------------
def suggest_foods(deficit_protein, deficit_carbs, deficit_fat, diet):
    foods = {
        "Non-Vegetarian": "- Grilled chicken breast (100g) → ~22g protein\n- 1 medium sweet potato → ~80g carbs\n- 1 tsp olive oil → ~5g fat",
        "Vegetarian": "- Paneer (100g) → ~22g protein\n- 2 slices whole wheat bread + 1 banana → ~80g carbs\n- 1 tsp olive oil → ~5g fat",
        "Vegan": "- Tofu (150g) → ~20g protein\n- Oats (60g) + blueberries → ~80g carbs\n- 1 tsp coconut oil → ~5g fat"
    }

    if deficit_protein <= 0 and deficit_carbs <= 0 and deficit_fat <= 0:
        return "✅ You’ve met all your macro requirements!"

    return f"""
You still need:
- Protein: {deficit_protein} g
- Carbohydrates: {deficit_carbs} g
- Fat: {deficit_fat} g

Suggested foods ({diet}):
{foods[diet]}
"""

# ------------------------
# Streamlit UI
# ------------------------
st.title(":weight_lifting_man: Get Set, Go!!!\nPerformance Driven Personalized Fuelling Requirements and Macro Tracker")

# --------- Workout details inputs ---------
st.subheader("Step 1: Workout Details")
sport_choice = st.selectbox("Select your sport", ["Swimming", "Running", "Cycling", "Gym/Strength Training", "Triathlon"])
intensity = st.selectbox("Select workout intensity", ["Low", "Moderate", "High", "Extreme"])
weight = st.number_input("Enter your weight (kg)", min_value=30.0, max_value=150.0, value=70.0, step=0.5)
gender = st.radio("Select your gender", ["Male", "Female"])
duration = st.number_input("Enter workout duration (hours)", min_value=0.5, max_value=8.0, value=2.0, step=0.5)
goal = st.radio("Select your goal", ["Performance", "Weight Loss / Body Composition"])
diet_choice = st.radio("Select your diet preference:", ["Non-Vegetarian", "Vegetarian", "Vegan"])

# --------- Current macro intake ---------
st.subheader("Step 2: Current Macro Intake")
intake_carbs = st.number_input("Carbohydrates consumed (g)", min_value=0, value=0, step=5)
intake_protein = st.number_input("Protein consumed (g)", min_value=0, value=0, step=5)
intake_fat = st.number_input("Fat consumed (g)", min_value=0, value=0, step=1)

# --------- Calculate button ---------
if st.button("Calculate Fueling Requirements"):
    results = fueling_requirements(intensity, weight, duration, gender, goal)

    # Step 3: Daily requirements
    st.subheader("Step 3: Your Daily Fueling Requirements")
    st.write(f"Carbohydrates: {results['carbs_g_range'][0]}-{results['carbs_g_range'][1]} g")
    st.write(f"Protein: {results['protein_g_range'][0]}-{results['protein_g_range'][1]} g")
    st.write(f"Fat: {results['fat_g_range'][0]}-{results['fat_g_range'][1]} g")
    st.write(f"Fluids lost: {results['fluid_loss_ml']} ml → Replace with ~{results['fluid_replacement_ml']} ml")
    st.write(f"Sodium: {results['sodium_mg']} mg")

    # Step 4: Macro deficits
    deficit_carbs = max(results["carbs_g_range"][0] - intake_carbs, 0)
    deficit_protein = max(results["protein_g_range"][0] - intake_protein, 0)
    deficit_fat = max(results["fat_g_range"][0] - intake_fat, 0)

    st.subheader("Step 4: Macro Deficit")
    st.write(f"Protein deficit: {deficit_protein} g")
    st.write(f"Carbohydrate deficit: {deficit_carbs} g")
    st.write(f"Fat deficit: {deficit_fat} g")

    # Step 5: Food suggestions
    st.subheader("Step 5: Food Suggestions")
    st.markdown(suggest_foods(deficit_protein, deficit_carbs, deficit_fat, diet_choice))

# --------- Feedback Form ---------
# ----------- FEEDBACK FORM SECTION -----------
