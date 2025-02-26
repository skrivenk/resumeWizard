import os
import openai
import json
import time
from dotenv import load_dotenv

# Load API Key
env_path = "D:/python_projects/resumeWizard/api.env"
load_dotenv(env_path)

API_KEY = os.getenv("OPENAI_API_KEY")

# Ensure API key is valid
if API_KEY is None or not API_KEY.startswith("sk-"):
    raise ValueError("Error: API Key not found or incorrect! Check api.env file.")

# Initialize OpenAI client
client = openai.OpenAI(api_key=API_KEY)

# Separate last request times for different functions
LAST_ANALYZE_REQUEST_TIME = 0
LAST_GENERATE_REQUEST_TIME = 0

def analyze_job_description(job_description):
    """Extract key skills from a job description using OpenAI."""
    global LAST_ANALYZE_REQUEST_TIME
    current_time = time.time()

    # Prevent excessive API calls
    if current_time - LAST_ANALYZE_REQUEST_TIME < 5:
        return {"error": "Slow down! You can only analyze a job description every 5 seconds."}

    LAST_ANALYZE_REQUEST_TIME = current_time  # Update request time

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Extract key skills from job descriptions and return as a JSON list."},
                {"role": "user", "content": f"Extract key skills from this job description:\n{job_description}.\n"
                                            "Respond only in JSON format: {\"skills\": [\"skill1\", \"skill2\", \"skill3\"]}"}
            ],
            max_tokens=100
        )

        extracted_text = response.choices[0].message.content.strip()

        # Ensure the response is valid JSON
        try:
            skills_list = json.loads(extracted_text)
            if isinstance(skills_list, dict) and "skills" in skills_list:
                return skills_list
            else:
                return {"error": "Unexpected AI response format"}
        except json.JSONDecodeError:
            return {"error": "AI response is not valid JSON"}

    except openai.APIConnectionError:
        return {"error": "Failed to connect to OpenAI servers. Check your internet connection."}
    except openai.RateLimitError:
        return {"error": "Too many requests! Please wait before trying again."}
    except openai.AuthenticationError:
        return {"error": "Invalid OpenAI API key. Check your `api.env` file."}
    except Exception as e:
        return {"error": str(e)}

def generate_resume(job_description, selected_experiences, creativity_level=0.5, resume_style="Professional"):
    """Generate a tailored resume using AI with user customization."""
    global LAST_GENERATE_REQUEST_TIME
    current_time = time.time()

    # Prevent excessive API calls
    if current_time - LAST_GENERATE_REQUEST_TIME < 5:
        return {"error": "Slow down! You can only generate a resume every 5 seconds."}

    LAST_GENERATE_REQUEST_TIME = current_time  # Update request time

    # Extract key skills from job description
    ai_result = analyze_job_description(job_description)

    if "error" in ai_result:
        return {"error": ai_result["error"]}

    extracted_skills = ai_result["skills"]

    # Format selected job experiences for AI input
    formatted_experiences = "\n".join(
        [f"- {job_title} at {company}: {responsibilities}" for job_title, company, responsibilities in selected_experiences]
    )

    # Adjust AI Temperature (Creativity)
    ai_temperature = creativity_level  # Ranges from 0.0 (strict) to 1.0 (creative)

    # Customize Resume Style
    style_instructions = {
        "Professional": "Use formal, business-oriented language.",
        "Casual": "Use a conversational, friendly tone.",
        "Technical": "Include detailed technical terminology.",
        "Concise": "Keep sentences short and remove unnecessary words."
    }
    style_instruction = style_instructions.get(resume_style, "Use a balanced, professional style.")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": f"You are an AI that rewrites job experience descriptions to match a job description. "
                            f"{style_instruction}"},
                {"role": "user", "content": f"""
                Given the following job description:

                {job_description}

                And these user-selected job experiences:

                {formatted_experiences}

                **Rewrite these experiences to be more relevant to the job description.**
                - Keep them realistic.
                - Use strong action verbs.
                - Focus on achievements and relevant skills.
                - {style_instruction}

                **Return only the rewritten experiences in structured text format.**
                """}
            ],
            max_tokens=500,
            temperature=ai_temperature  # Adjusted by user selection
        )

        generated_experiences = response.choices[0].message.content.strip()

        # Final resume formatting
        final_resume = f"""
        **Name:** Sergei Krivenkov
        **Phone:** 720-560-9915
        **Email:** sergei.krivenkov@gmail.com
        **Website:** sergeik.com

        **Professional Summary:**  
        (AI-generated based on job description)

        **Technical Skills:**  
        - {', '.join(extracted_skills)}

        **Professional Experience:**  
        {generated_experiences}

        **Projects & Independent Initiatives:**  
        - Virtualized Lab Environment (Proxmox Cluster)  
        - Job Search Java Application  
        - Personal Blog & Portfolio (sergeik.com)  

        **Education & Certifications:**  
        - Metropolitan State University of Denver – Bachelor of Science in Computer Information Systems (2019)  
        - CompTIA Security+ (2024)  
        - CompTIA A+ (2024)  
        - VMware Certified Professional – Data Center Virtualization (2019 & 2021)  
        """

        return {"resume": final_resume}

    except Exception as e:
        return {"error": str(e)}
