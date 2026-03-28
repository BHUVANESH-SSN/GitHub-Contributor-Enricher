import json
from datetime import datetime

def extract_profile(profile):
    data = profile.get("data", {})

    # Full name
    full_name = f"{data.get('firstName', '')} {data.get('lastName', '')}".strip()

    # LinkedIn URL
    linkedin_url = data.get("linkedinUrl")

    # Experience
    experience = data.get("experience", [])
    if not experience:
        return None

    latest = experience[0]

    title = latest.get("title")
    company = latest.get("companyName")

    start = latest.get("startEndDate", {}).get("start")
    end = latest.get("startEndDate", {}).get("end")

    try:
        start_year = datetime.fromisoformat(start.replace("Z", "")).year if start else None

        if end:
            end_year = datetime.fromisoformat(end.replace("Z", "")).year
            duration = f"{start_year} - {end_year}"
        else:
            duration = f"{start_year} - Current"
    except:
        duration = "Unknown"

    return {
        "full_name": full_name,
        "company": company,
        "title": title,
        "experience_years": duration,
        "linkedin_url": linkedin_url
    }


# 🔹 Load your JSON file
with open("reverse_connect.json", "r") as f:
    profiles = json.load(f)

results = []

# 🔹 Process all profiles
for profile in profiles:
    extracted = extract_profile(profile)
    if extracted:
        results.append(extracted)

# 🔹 Save output
with open("final_output.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"✅ Converted {len(results)} profiles successfully!")