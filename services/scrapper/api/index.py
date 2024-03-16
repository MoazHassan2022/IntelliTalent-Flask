from .scrapped_websites.linkedin import linkedin_scrape_thread
from .scrapped_websites.wuzzuf import wuzzuf_scrape_thread
from .app import db_name
from flask import current_app as app
from .logger import logger
import _thread, json
    
def health_check():
    logger.debug("Health check")
    return "Hello World From Scrapper Service!"

def scrape():
    """
    Start the scraping process
    Args:
        None
    Returns:
        dict: A dictionary containing the status of the scraping process
    """
    # Connect to MongoDB, at unstructured jobs db
    unstructured_jobs_db = app.mongo[db_name]
    
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