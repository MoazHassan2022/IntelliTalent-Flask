from ..logger import logger
from instance import config
from ..unstructured_jobs.unstructured_jobs_service import insert_jobs
from bs4 import BeautifulSoup
import requests
import time as tm
from urllib.parse import quote
from itertools import groupby

# Constants

# Number of times to try the same query (linkedin gives different results each time)
ROUNDS = 1

# Number of times to retry to connect to the same url
RETRIES = 4
DELAY = 2

# 1: onsite - 2: remote - 3: hybrid
JOB_PLACES = [1, 2, 3]

JOB_PLACES_MAP = {
    1: "On Site",
    2: "Remote",
    3: "Hybrid",
}

# Max number of days to scrape (take only the last DAYS_TO_SCRAPE days) 
DAYS_TO_SCRAPE = 1

def get_with_retry(url, retries=RETRIES, delay=DELAY):
    """
    Get the URL with retries and delay
    Args:
        url (str): The URL to get
        retries (int): The number of times to retry to connect to the same url
        delay (int): The delay between retries
    Returns:
        BeautifulSoup: The beautiful soup object
    """
    # Get the URL with retries and delay
    for _ in range(retries):
        try:
            r = requests.get(url)
            return BeautifulSoup(r.content, "html.parser")
        except requests.exceptions.Timeout:
            logger.debug(f"Timeout in getting URL: {url}, retrying")
            tm.sleep(delay)
        except Exception as e:
            logger.error(f"Error in getting URL: {url}")
            logger.exception(e)
    return None

def get_job_cards_main_info(soup, place):
    """
    Get the job card info from the search results page
    Args:
        soup (BeautifulSoup): The beautiful soup object
        place (int): The place of the job (1: On Site, 2: Remote, 3: Hybrid)
    Returns:
        list: The list of job cards
    """
    jobs = []

    try:
        divs = soup.find_all("div", class_="base-search-card__info")
    except:
        logger.error("no jobs found")
        return jobs

    for item in divs:
        job_title = item.find("h3").text.strip()
        
        company_name = item.find("a", class_="hidden-nested-link")
        
        job_location = item.find("span", class_="job-search-card__location")
        
        date_new_class = item.find("time", class_ = "job-search-card__listdate--new")
        
        date_old_class = item.find("time", class_="job-search-card__listdate")
        
        date = date_old_class["datetime"] if date_old_class else date_new_class["datetime"] if date_new_class else ""
        
        # Get the job posting id
        parent_div = item.parent
        entity_urn = parent_div["data-entity-urn"]
        job_posting_id = entity_urn.split(":")[-1]
        
        # Construct job url
        job_url = f"http://www.linkedin.com/jobs/view/{job_posting_id}/"
        
        job = {
            "jobId": job_posting_id,
            "title": job_title,
            "company": company_name.text.strip().replace("\n", " ") if company_name else "",
            "jobLocation": job_location.text.strip() if job_location else "",
            "publishedAt": date,
            "url": job_url,
            "jobPlace": JOB_PLACES_MAP[place],
        }
        jobs.append(job)
    return jobs

def clean_text(text):
    return (text.replace("\n\n", "")
                .replace("::marker", "-")
                .replace("-\n", "- ")
                .replace("Show less", "")
                .replace("Show more", ""))

def get_job_description(soup):
    """
    Get the job description from the job page
    Args:
        soup (BeautifulSoup): The beautiful soup object
    Returns:
        str: The job description
    """
    div = soup.find("div", class_="description__text description__text--rich")
    if div:
        for element in div.find_all(["span", "a", "ul"]):
            if element.name in ["span", "a"]:
                element.decompose()
            else:  # handling 'ul' elements
                for li in element.find_all("li"):
                    li.insert(0, "-")

        text = div.get_text(separator="\n").strip()
        text = clean_text(text)
        return text
    else:
        logger.error("(LinkedIn) no job description, retrying...")
        return "no job description"

def get_search_queries():
    """
    Get the search queries to use
    Args:
        None
    Returns:
        list: The list of search queries
    """
    titles = config.JOB_TITLES
    locations = config.JOB_LOCATIONS
    places = JOB_PLACES

    search_queries = []

    for title in titles:
        for location in locations:
            for place in places:
                search_queries.append({
                    "keywords": title,
                    "location": location,
                    "place": place
                })
                
    return search_queries

def sort_and_group_key(item):
    return item["title"], item["company"]

def remove_duplicates(jobs):
    """
    Remove duplicate jobs in the jobs
    Args:
        jobs (list): The list of jobs
    Returns:
        list: The list of jobs with duplicates removed
    """
    jobs.sort(key=sort_and_group_key)
    jobs = [next(group) for _, group in groupby(jobs, key=sort_and_group_key)]
    return jobs

def get_job_cards(search_queries, rounds = ROUNDS, pages_to_scrape = config.PAGES_TO_SCRAPE):
    """
    Get the job cards from the search results page
    Args:
        search_queries (list): The list of search queries to use
        rounds (int): The number of times to try the same query
        pages_to_scrape (int): The
    Returns:
        list: The list of job cards
    """
    # Function to get the job cards from the search results page
    all_jobs = []
    
    for _ in range(0, rounds):
        for query in search_queries:
            keywords = quote(query["keywords"]) # URL encode the keywords
            location = quote(query["location"]) # URL encode the location
            place = query["place"]
            timespan = "r" + str(DAYS_TO_SCRAPE * 24 * 60 * 60)
            
            for i in range (0, pages_to_scrape):
				# Construct the URL
                url = f"http://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keywords}&location={location}&f_WT={place}&f_TPR={timespan}&start={25*i}"

                soup = get_with_retry(url)
                jobs = get_job_cards_main_info(soup, place)
                
                if len(jobs) == 0:
                    logger.debug("(LinkedIn) No jobs found on page: %s", url)
                    break
                
                all_jobs = all_jobs + jobs
                
                logger.debug("(LinkedIn) Finished scraping page: %s", url)
	
    logger.debug("(LinkedIn) Total job cards scraped: %s", len(all_jobs))

    all_jobs = remove_duplicates(all_jobs)
    logger.debug("(LinkedIn) Total job cards after removing duplicates: %s", len(all_jobs))
    
    return all_jobs

def linkedin_scrape_thread(unstructured_jobs_db):
    """
    The main linkedin scraping function
    Args:
        unstructured_jobs_db (MongoClient): The unstructured jobs database
    Returns:
        None
    """
    start = tm.perf_counter()
    job_list = []

    search_queries = get_search_queries()
    all_jobs = get_job_cards(search_queries)

    if len(all_jobs) > 0:
        for job in all_jobs:
            logger.debug(f"(LinkedIn) Found new job: {job['title']}, at {job['company']}, url: {job['url']}")
            
            for _ in range(RETRIES):
                # Get the job description
                description_soup_object = get_with_retry(job["url"])
                
                job["description"] = get_job_description(description_soup_object)
                
                if job["description"] != "no job description":
                    break
            
            job_list.append(job)
            
        # insert in db, note that there is an index on title, company, and publishedAt fields, that handls duplicated jobs
        insert_jobs(unstructured_jobs_db, job_list)
    else:
        logger.debug("(LinkedIn) No jobs found")
    
    end = tm.perf_counter()
    logger.info(f"Scraping LinkedIn finished in {end - start:.2f} seconds")
    
def check_closed_class(soup):
    """
    Check if the job is closed
    Args:
        soup (BeautifulSoup): The beautiful soup object
    Returns:
        bool: False if the job is closed, True otherwise
    """
    # Check if the job is closed
    selected_elements = soup.select(".closed-job")
    return len(selected_elements) == 0

def linkedin_check_active_jobs(jobs):
    """
    Check the active jobs
    Args:
        jobs (list): The list of jobs
    Returns:
        dict: A dictionary containing the jobs status
    """
    # This is not a 100% accurate method to check if the job is active or not, 
    # because linkedin sometimes return empty page for the job in the request,
    # Check the active jobs
    for job in jobs:
        # Get the job status
        job_page_soup = get_with_retry(job["url"])
        if job_page_soup is None:
            job["isActive"] = False
            del job["url"]
            del job["jobId"]
            continue
        
        job["isActive"] = check_closed_class(job_page_soup)
        del job["url"]
        del job["jobId"]
    
    return jobs
