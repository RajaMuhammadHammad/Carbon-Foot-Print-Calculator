from flask import Flask, render_template, request, redirect, url_for, session
import os, json
import google.generativeai as genai  
from google.generativeai import types  



app = Flask(__name__)
app.secret_key = "secret_key"  

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Load Scope 2 JSON
with open(os.path.join(DATA_DIR, "scope2.json"), "r") as f:
    scope2_data = json.load(f)

# Load Scope 1 JSON
with open(os.path.join(DATA_DIR, "scope1.json"), "r") as f:
    data = json.load(f)

# Load Scope 3 JSON
with open(os.path.join(DATA_DIR, "scope3", "scope3.json"), "r") as f:
    scope3_json = json.load(f)
    scope3_data = scope3_json["Scope3"]  

scope1_data = data["scope1"]  

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# ----------------- ROUTES -----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# -------- SCOPE 1 --------
@app.route("/scope1", methods=["GET", "POST"])
def scope1():
    results = []
    total_emission = 0.0

    if request.method == "POST":
        # Loop through all categories at once
        for category in scope1_data:
            cat_name = category["category"]

            # -------- Stationary Combustion --------
            for fuel in category.get("fuels", []):
                name = fuel["name"]
                qty = request.form.get(f"qty_{name}")
                unit = request.form.get(f"unit_{name}")

                if qty and unit:
                    try:
                        qty_val = float(qty)
                        factor = fuel["units"].get(unit)
                        if factor and qty_val > 0:
                            emission = round(qty_val * factor, 2)
                            results.append({
                                "category": cat_name,
                                "item": name,
                                "unit": unit,
                                "qty": qty_val,
                                "factor": factor,
                                "emission": emission
                            })
                            total_emission += emission
                    except ValueError:
                        continue

            # -------- Mobile Emissions --------
            for vehicle, fuels_list in category.get("vehicles", {}).items():
                for fuel in fuels_list:
                    name = f"{vehicle} - {fuel['fuel']}"
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * fuel["emission_factor"], 2)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": fuel["unit"],
                                    "qty": qty_val,
                                    "factor": fuel["emission_factor"],
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue

            # -------- Fugitive Emissions --------
            for chem in category.get("chemicals", []):
                name = chem["name"]
                qty = request.form.get(f"qty_{name}")

                if qty:
                    try:
                        qty_val = float(qty)
                        if qty_val > 0:
                            emission = round(qty_val * chem["emission_factor"])
                            results.append({
                                "category": cat_name,
                                "item": name,
                                "unit": chem["unit"],
                                "qty": qty_val,
                                "factor": chem["emission_factor"],
                                "emission": emission
                            })
                            total_emission += emission
                    except ValueError:
                        continue

            # -------- Industrial Process Emissions --------
            for process in category.get("processes", []):
                name = process["name"]
                qty = request.form.get(f"qty_{name}")

                if qty:
                    try:
                        qty_val = float(qty)
                        if qty_val > 0:
                            emission = round(qty_val * process["emission_factor"])
                            results.append({
                                "category": cat_name,
                                "item": name,
                                "unit": process["unit"],
                                "qty": qty_val,
                                "factor": process["emission_factor"],
                                "emission": emission
                            })
                            total_emission += emission
                    except ValueError:
                        continue



        total_emission = round(total_emission, 2)
        # Save Scope 1 results to session for summary
        session["scope1_results"] = results
        session["scope1_total"] = total_emission

        return render_template(
            "scope1.html",
            categories=scope1_data,
            results=results,
            total=total_emission
        )

    # GET request
    return render_template("scope1.html", categories=scope1_data, results=None)

# -------- Scope 2 --------
@app.route("/scope2", methods=["GET", "POST"])
def scope2():
    results = []
    total_emission = 0.0

    if request.method == "POST":
        selected_countries = request.form.getlist("countries")
        for country in selected_countries:
            qty = request.form.get(f"qty_{country}")
            if qty and qty.strip():
                try:
                    qty_val = float(qty)
                    factor = scope2_data[country]["factor"]
                    unit = scope2_data[country]["unit"]
                    emission = round(qty_val * factor, 2)
                    results.append({
                        "country": country,
                        "unit": unit,
                        "qty": qty_val,
                        "factor": factor,
                        "emission": emission
                    })
                    total_emission += emission
                except ValueError:
                    continue

         # Save Scope 2 to session for summary
        
        total_emission = round(total_emission, 2)
        session["scope2_results"] = results
        session["scope2_total"] = total_emission


        return render_template(
            "scope2.html",
            countries=scope2_data,
            selected=request.form.getlist("countries"),
            results=results,
            total=total_emission
        )

    return render_template("scope2.html", countries=scope2_data, selected=None)

# -------- SCOPE 3 ROUTE --------
@app.route("/scope3", methods=["GET", "POST"])
def scope3():
    results = []
    total_emission = 0.0

    if request.method == "POST":

        # -------- Purchased Goods & Services --------
        for category in scope3_data:
            if category["Category"] == "Purchased goods & services":
                cat_name = category["Category"]
                for item in category.get("Product/Service", []):
                    name = item["Product/Service"]
                    unit = item["Unit"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": unit,
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue

        # -------- Transportation & Logistics Services --------
        for category in scope3_data:
            if category["Category"] == "Transportation & Logistics Services":
                cat_name = category["Category"]
                for item in category.get("Product/Service", []):
                    name = item["Product/Service"]
                    unit = item["Unit"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": unit,
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue

        # -------- Publishing Services --------
        for category in scope3_data:
            if category["Category"] == "Publishing Services":
                cat_name = category["Category"]
                for item in category.get("Publishing Services", []):
                    name = item["Product/Service"]
                    unit = item["Unit"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": unit,
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue

        # -------- Financial & Insurance Services --------
        for category in scope3_data:
            if category["Category"] == "Financial & Insurance Services":
                cat_name = category["Category"]
                for item in category.get("Financial & Insurance Services", []):
                    name = item["Product/Service"]
                    unit = item["Unit"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": unit,
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue

        # -------- Real Estate & Leasing Services --------
        for category in scope3_data:
            if category["Category"] == "Real Estate & Leasing Services":
                cat_name = category["Category"]
                for item in category.get("Real Estate & Leasing Services", []):
                    name = item["Product/Service"]
                    unit = item["Unit"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": unit,
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue

        # -------- Professional, Scientific & Technical Services --------
        for category in scope3_data:
            if category["Category"] == "Professional, Scientific & Technical Services":
                cat_name = category["Category"]
                for item in category.get("Professional, Scientific & Technical Services", []):
                    name = item["Product/Service"]
                    unit = item["Unit"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": unit,
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue

        # -------- Business Support & Administrative Services --------
        for category in scope3_data:
            if category["Category"] == "Business Support & Administrative Services":
                cat_name = category["Category"]
                for item in category.get("Business Support & Administrative Services", []):
                    name = item["Product/Service"]
                    unit = item["Unit"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": unit,
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue

        # -------- Waste Management & Remediation Services --------
        for category in scope3_data:
            if category["Category"] == "Waste Management & Remediation Services":
                cat_name = category["Category"]
                for item in category.get("Waste Management & Remediation Services", []):
                    name = item["Product/Service"]
                    unit = item["Unit"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": unit,
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue


        
        # -------- Educational Services--------
        for category in scope3_data:
            if category["Category"] == "Educational Services":
                cat_name = category["Category"]
                for item in category.get("Educational Services", []):
                    name = item["Product/Service"]
                    unit = item["Unit"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": unit,
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue       



        
        # -------- Healthcare & Social Assistance Services --------
        for category in scope3_data:
            if category["Category"] == "Healthcare & Social Assistance Services":
                cat_name = category["Category"]
                for item in category.get("Healthcare & Social Assistance Services", []):
                    name = item["Product/Service"]
                    unit = item["Unit"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": unit,
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue   


            
        # -------- Arts, Entertainment & Recreation Services--------
        for category in scope3_data:
            if category["Category"] == "Arts, Entertainment & Recreation Services":
                cat_name = category["Category"]
                for item in category.get("Arts, Entertainment & Recreation Services", []):
                    name = item["Product/Service"]
                    unit = item["Unit"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": unit,
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue      
        
        



        # -------- Accommodation & Food Services --------
        for category in scope3_data:
            if category["Category"] == "Accommodation & Food Services":
                cat_name = category["Category"]
                for item in category.get("Accommodation & Food Services", []):
                    name = item["Product/Service"]
                    unit = item["Unit"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": unit,
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue


        
        # -------- Repair & Maintenance Services --------
        for category in scope3_data:
            if category["Category"] == "Repair & Maintenance Services":
                cat_name = category["Category"]
                for item in category.get("Repair & Maintenance Services", []):
                    name = item["Product/Service"]
                    unit = item["Unit"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": unit,
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue

        # -------- Personal Care & Other Personal Services --------
        for category in scope3_data:
            if category["Category"] == "Personal Care & Other Personal Services":
                cat_name = category["Category"]
                for item in category.get("Personal Care & Other Personal Services", []):
                    name = item["Product/Service"]
                    unit = item["Unit"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": unit,
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue



                # -------- Membership Organizations & Associations --------
        for category in scope3_data:
            if category["Category"] == "Membership Organizations & Associations":
                cat_name = category["Category"]
                for item in category.get("Membership Organizations & Associations", []):
                    name = item["Product/Service"]
                    unit = item["Unit"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": unit,
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue

        for category in scope3_data:
            if category["Category"] == "Capital Goods":
                cat_name = category["Category"]

                for item in category.get("Capital Goods", []):
                    name = item["Product/Service"]
                    factor = item["EmissionFactor"]
                    qty = request.form.get(f"qty_{name}")

                    if qty:
                        try:
                            qty_val = float(qty)
                            if qty_val > 0:
                                emission = round(qty_val * factor)
                                results.append({
                                    "category": cat_name,
                                    "item": name,
                                    "unit": "USD",        # <-- Hardcoded here
                                    "qty": qty_val,
                                    "factor": factor,
                                    "emission": emission
                                })
                                total_emission += emission
                        except ValueError:
                            continue

        total_emission = round(total_emission, 2)                
                # -------- Store Results --------
        session["scope3_results"] = results
        session["scope3_total"] = total_emission

        return render_template(
            "scope3.html",
            categories=scope3_data,
            results=results,
            total=total_emission
        )

    # GET request
    return render_template("scope3.html", categories=scope3_data, results=None)


@app.route("/scope3_summary")
def scope3_summary():
    results = session.get("scope3_results", [])
    
    # Only include items where qty > 0
    entered_results = [r for r in results if r.get("qty", 0) > 0]
    
    # Grand total
    total = sum(r.get("emission", 0.0) for r in entered_results)
    
    return render_template("scope3_summary.html", results=entered_results, total=total)



# ----------------- Summary Input Form -----------------
@app.route("/summary", methods=["GET", "POST"])
def summary():
    if request.method == "POST":
        # Collect user inputs
        session["total_revenue"] = float(request.form.get("revenue") or 0)
        session["total_employees"] = int(request.form.get("employees") or 1)
        session["target_emission"] = float(request.form.get("target_emission") or 0)
        return redirect(url_for("dashboard"))

    return render_template("summary_input.html") 












def aggregate_top_sources():
    """
    Read the session-stored results from scope1, scope2, scope3,
    flatten them, sum by “category/item” or whichever grouping,
    sort descending, pick top 5.
    """
    all_items = []
    for key in ("scope1_results", "scope2_results", "scope3_results"):
        items = session.get(key, [])
        all_items.extend(items)
    agg = {}
    for it in all_items:
        key_name = f"{it.get('category','')} — {it.get('item','')}"
        val = it.get("emission", 0.0)
        agg[key_name] = agg.get(key_name, 0.0) + val
    # Sort by emission descending
    sorted_items = sorted(agg.items(), key=lambda x: x[1], reverse=True)
    top5 = sorted_items[:5]
    # Convert into list of dicts
    return [{"source": name, "value": value} for name, value in top5]

@app.route("/dashboard")
def dashboard():
    import google.generativeai as genai
    from google.generativeai import types

    # --- Totals ---
    total_scope1 = float(session.get("scope1_total") or 0.0)
    total_scope2 = float(session.get("scope2_total") or 0.0)
    total_scope3 = float(session.get("scope3_total") or 0.0)
    overall_total = total_scope1 + total_scope2 + total_scope3

    revenue = float(session.get("total_revenue") or 1)
    employees = int(session.get("total_employees") or 1)
    target_emission = float(session.get("target_emission") or 0)

    total_tonnes = overall_total / 1000  # Convert kg → tonnes

    # --- Derived Metrics ---
    emission_per_revenue = total_tonnes / revenue if revenue > 0 else 0
    emission_per_employee = total_tonnes / employees if employees > 0 else 0

    # --- Chart & Top Sources ---
    chart_data = {
        "labels": ["Scope 1", "Scope 2", "Scope 3"],
        "values": [total_scope1, total_scope2, total_scope3],
    }
    top_sources = aggregate_top_sources()

    # --- Gemini Setup ---
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("models/gemini-2.5-pro")

    # --- Gemini Prompt ---
    prompt = f"""
    You are a sustainability and environmental impact expert.

    The company reports:
    - Total Emissions: {overall_total:.2f} kgCO₂e (≈ {total_tonnes:.2f} tonnes)
    - Target Emissions: {target_emission:.2f} kgCO₂e

    Please provide:
    1️⃣ A short summary comparing total vs target (percentage difference).
    2️⃣ Three clear, actionable recommendations to reduce carbon emissions.

    Respond STRICTLY in JSON format:
    {{
      "comparison_to_target": "text summary",
      "recommendations": [
        "recommendation 1",
        "recommendation 2",
        "recommendation 3"
      ]
    }}
    """

    # --- Try AI Call ---
    try:
        response = model.generate_content(
            prompt,
            generation_config=types.GenerationConfig(
                temperature=0.3,
                top_p=0.9,
            ),
        )

        raw = response.text.strip()

        # Clean Markdown formatting if Gemini includes it
        if "```" in raw:
            raw = raw.split("```")[1]
            raw = raw.replace("json", "").strip()

        # Try to parse JSON
        ai_data = json.loads(raw)

    except Exception as e:
        print("⚠️ Gemini AI Error:", e)
        # --- Fallback text response ---
        try:
            # Ask again in plain text if JSON fails
            fallback_prompt = f"""
            Give 3 short and clear carbon reduction suggestions for a company
            emitting {total_tonnes:.2f} tonnes CO₂e with a target of {target_emission/1000:.2f} tonnes.
            """
            response2 = model.generate_content(fallback_prompt)
            ai_data = {
                "comparison_to_target": f"Emissions {total_tonnes:.2f} tCO₂e vs Target {target_emission/1000:.2f} tCO₂e",
                "recommendations": [r.strip() for r in response2.text.split("\n") if r.strip()][:3],
            }
        except Exception:
            ai_data = {
                "comparison_to_target": "Unable to generate AI insights.",
                "recommendations": [
                    "Review energy consumption in key facilities.",
                    "Switch to renewable power sources.",
                    "Improve operational efficiency through audits."
                ]
            }

    # --- Pass Data to Template ---
    return render_template(
        "dashboard.html",
        total_scope1=total_scope1,
        total_scope2=total_scope2,
        total_scope3=total_scope3,
        overall_total=overall_total,
        emission_per_revenue=emission_per_revenue,
        emission_per_employee=emission_per_employee,
        chart_data=chart_data,
        top_sources=top_sources,
        target_emission=target_emission,
        ai_comparison=ai_data,
    )



# ----------------- RUN APP -----------------
if __name__ == "__main__":
    app.run(debug=True)