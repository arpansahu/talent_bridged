from jobs.documents import JobDocument

def search_jobs(query):
    """
    This function performs a full-text search on the 'job_post' field in the JobDocument index.
    It returns a queryset of jobs that match the query.
    """

    # Perform a match query on the 'job_post' field
    search = JobDocument.search().query("match", post_text=query)
    
    # Return the queryset of matching jobs
    return search.to_queryset()
