from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from jobspy import scrape_jobs

app = FastAPI(title="JobSpy Private API")

# Define what n8n will send to our API
class JobRequest(BaseModel):
    search_terms: list[str]
    locations: list[str]

@app.post("/scrape")
def scrape_jobs_endpoint(req: JobRequest):
    all_jobs_list = []
    
    for term in req.search_terms:
        for loc in req.locations:
            try:
                jobs = scrape_jobs(
                    site_name=["indeed", "linkedin"],
                    search_term=term,
                    location=loc,
                    results_wanted=5,
                    hours_old=24,
                    country_indeed='USA'
                )
                if not jobs.empty:
                    all_jobs_list.append(jobs)
            except Exception as e:
                print(f"Error scraping {term} in {loc}: {e}")

    # If nothing was found, return an empty array
    if not all_jobs_list:
        return []

    # Combine and clean the data
    all_jobs_df = pd.concat(all_jobs_list, ignore_index=True)
    all_jobs_df = all_jobs_df.drop_duplicates(subset=['job_url'])
    all_jobs_df = all_jobs_df.fillna("")

    # Convert dates to strings to prevent JSON errors (FastAPI handles the actual JSON conversion)
    if 'date_posted' in all_jobs_df.columns:
        all_jobs_df['date_posted'] = all_jobs_df['date_posted'].astype(str)

    return all_jobs_df.to_dict(orient='records')