import aiohttp
import asyncio
import time

# Max retries and delay for rate-limited requests
MAX_RETRIES = 5
RETRY_DELAY = 2  # Seconds to wait before retrying

async def fetch_user_submission(session, user):
    """
    Fetch submissions for a single user with rate-limit handling and distinct titles.
    """
    url = f"https://alfa-leetcode-api.onrender.com/{user}/acSubmission"  # Modify the URL if necessary
    retries = 0

    while retries < MAX_RETRIES:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()  # Assuming the response is in JSON format
                    distinct_submissions = get_distinct_submissions(data['submission'])
                    return {user: distinct_submissions}  # Return a dictionary with the user's submissions
                elif response.status == 429:  # Rate-limited error (too many requests)
                    # Get the "Retry-After" header if provided
                    retry_after = int(response.headers.get("Retry-After", RETRY_DELAY))
                    print(f"Rate limit exceeded for {user}. Retrying after {retry_after} seconds.")
                    time.sleep(retry_after)  # Wait before retrying
                    retries += 1
                else:
                    return {user: f"Failed with status {response.status}"}

        except Exception as e:
            return {user: f"Error: {str(e)}"}

    return {user: "Max retries reached. Rate limit not cleared."}


def get_distinct_submissions(submissions):
    """
    Extract distinct submissions based on the 'titleSlug' field.
    """
    seen_slugs = set()  # To keep track of unique 'titleSlug'
    distinct_submissions = []

    for submission in submissions:
        if submission['titleSlug'] not in seen_slugs:
            distinct_submissions.append(submission)
            seen_slugs.add(submission['titleSlug'])
    
    return distinct_submissions


async def fetch_submissions_for_users(user_list):
    """
    Fetch submissions for all users concurrently, with rate limit handling.
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        for user in user_list:
            tasks.append(fetch_user_submission(session, user))
        # Wait for all tasks to complete and return the results
        results = await asyncio.gather(*tasks)
        return results
