from .logger import logger
import json

from .helpers.helper import extract_job_titles, extract_skills, extract_locations, extract_job_types, extract_years_of_experience, extract_job_end_dates, extract_company_names, extract_countries_cities, extract_languages
    
def health_check():
    logger.debug("Health check")
    return "Hello World From Custom Job Service!"


def create_custom_job(data):
    """
    return structured job details based on the job prompt using NLP techniques

    Args:
        data (string): prompt for the job
    Returns:
        serialized json : structured job details
    """
    logger.debug("Create custom job")
    prompt = data['jobPrompt']

    countries, cities = extract_countries_cities(prompt)

    extracted_job_titles = extract_job_titles(prompt)
    extracted_skills = extract_skills(prompt)
    extracted_locations = extract_locations(prompt)
    extracted_job_types = extract_job_types(prompt)
    extracted_years_of_experience = extract_years_of_experience(prompt)
    extracted_job_end_dates = extract_job_end_dates(prompt)
    extracted_company_names = extract_company_names(prompt)
    extracted_languages = extract_languages(prompt)


    job = {
        "title": extract_job_titles(prompt)[0] if len(extracted_job_titles) > 0 else None,
        "skills": extract_skills(prompt),
        "jobLocation": extract_locations(prompt)[0] if len(extracted_locations) > 0 else None,
        "type": extract_job_types(prompt)[0] if len(extracted_job_types) > 0 else None,
        "neededExperience": extract_years_of_experience(prompt)[0].split("-")[0] if len(extracted_years_of_experience) > 0 else None,
        "jobEndDate": extract_job_end_dates(prompt)[0] if len(extracted_job_end_dates) > 0 else None,
        "company": extract_company_names(prompt)[0] if len(extracted_company_names) > 0 else None,
        "city": cities if len(cities) > 0 else None,
        "country": countries if len(countries) > 0 else None,
        "languages": extract_languages(prompt) if len(extracted_languages) > 0 else None
    }

    return json.dumps({
        "job": job
    })
