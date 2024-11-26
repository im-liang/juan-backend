import aiohttp
import asyncio
import time
import logging
from datetime import datetime, timezone

# Configure logging
logger = logging.getLogger("leetcode")

# Max retries and delay for rate-limited requests
MAX_RETRIES = 5
RETRY_DELAY = 2  # Seconds to wait before retrying

async def fetch_user_submission(session, username):
    """
    Fetch submissions for a single user with rate-limit handling and distinct titles.

    Args:
        session (aiohttp.ClientSession): The aiohttp session for HTTP requests.
        username (str): LeetCode username.

    Returns:
        dict: A dictionary containing the user's submissions or an error message.
    """
    url = f"https://alfa-leetcode-api.onrender.com/{username}/acSubmission"
    retries = 0
    logger.info(f"About to make request to {url}")

    while retries < MAX_RETRIES:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()  # Assuming the response is in JSON format
                    today_unique_submissions = get_today_unique_submissions(username, data["submission"])
                    logger.info(f"submission list: {today_unique_submissions}")
                    return today_unique_submissions
                elif response.status == 429:  # Rate-limited error (too many requests)
                    retry_after = int(response.headers.get("Retry-After", RETRY_DELAY))
                    logger.info(f"Rate limit exceeded for {username}. Retrying after {retry_after} seconds.")
                    time.sleep(retry_after)
                    retries += 1
                else:
                    return {"leetcode_username": username, "error": f"Failed with status {response.status}"}

        except Exception as e:
            logger.error(f"Error fetching submissions for {username}: {str(e)}")
            return {"leetcode_username": username, "error": str(e)}

    return {"leetcode_username": username, "error": "Max retries reached. Rate limit not cleared."}


def get_today_unique_submissions(username, submissions):
    """
    Get unique submissions for the current day (UTC) for the given user.

    Args:
        username (str): The LeetCode username.
        submissions (list): List of submissions returned by the API.

    Returns:
        dict: A dictionary containing the username and today's unique submissions (titles only).
    """
    today = datetime.now(timezone.utc).date()  # Current date in UTC
    seen_slugs = set()  # To track unique titleSlug values
    today_submissions = []

    for submission in submissions:
        # Convert timestamp to a date
        timestamp = int(submission.get("timestamp", 0))
        submission_date = datetime.fromtimestamp(timestamp, tz=timezone.utc).date()

        # Check if submission was made today and is unique
        title_slug = submission.get("titleSlug")
        if submission_date == today and title_slug not in seen_slugs:
            seen_slugs.add(title_slug)
            today_submissions.append(submission.get("title"))  # Collect only the title

    if not today_submissions:
        today_submissions.append("None")
        
    return {
        "leetcode_username": username,
        "today_submissions": today_submissions  # List of titles only
    }


async def fetch_submissions_for_users(user_list):
    """
    Fetch submissions for all users concurrently, with rate limit handling.

    Args:
        user_list (list): List of LeetCode usernames.

    Returns:
        list: A list of dictionaries containing each user's unique submissions for today.
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        for user in user_list:
            logger.info(f"Processing submissions for user: {user}")
            tasks.append(fetch_user_submission(session, user['leetcode_username']))
        results = await asyncio.gather(*tasks)
        return results
