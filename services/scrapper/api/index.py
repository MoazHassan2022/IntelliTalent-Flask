from .scrapped_websites.linkedin import (
    linkedin_scrape_thread,
    linkedin_check_active_jobs,
)
from .scrapped_websites.wuzzuf import (
    wuzzuf_scrape_thread,
    wuzzuf_check_active_jobs,
)
from .logger import logger
import _thread, json

def health_check():
    logger.debug("Health check")
    return "Hello World From Scrapper Service!"

def scrape(unstructured_jobs_db):
    """
    Start the scraping process
    Args:
        unstructured_jobs_db (MongoClient): The unstructured jobs database
    Returns:
        dict: A dictionary containing the status of the scraping process
    """
    # Start the scraping threads
    # Start the linkedin scraping thread
    _thread.start_new_thread(
            # don't remove the comma, it's needed to pass the db as an argument, and not to destruct it
            linkedin_scrape_thread, (unstructured_jobs_db,)
        )
    
    # Start the wuzzuf scraping thread
    _thread.start_new_thread(
            # don't remove the comma, it's needed to pass the db as an argument, and not to destruct it
            wuzzuf_scrape_thread, (unstructured_jobs_db,)
        )
    
    return {
        "status": "success",
        "message": "scrapping started"
    }

def check_active_jobs(body):
    """
    Check the active jobs
    Args:
        body (dict): The dict with "jobs" key
    Returns:
        dict: A dictionary containing the jobs status
    """
    logger.info("Checking active jobs")
    
    all_jobs = body.get("jobs")
    
    if all_jobs is None:
        return {
            "error": "No jobs found"
        }
    
    # Extract each platform jobs
    linkedin_jobs = [job for job in all_jobs if "linkedin" in job["url"]]
    wuzzuf_jobs = [job for job in all_jobs if "wuzzuf" in job["url"]]
    
    # Check the linkedin jobs
    linkedin_jobs_updated = linkedin_check_active_jobs(linkedin_jobs)
    
    # Check the wuzzuf jobs
    wuzzuf_jobs_updated = wuzzuf_check_active_jobs(wuzzuf_jobs)
    
    # Merge the updated jobs
    all_jobs_updated = linkedin_jobs_updated + wuzzuf_jobs_updated
    
    # Check the active jobs
    return json.dumps({
        "jobs": all_jobs_updated
    })