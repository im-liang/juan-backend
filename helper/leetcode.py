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

# Define the API configurations with custom response handlers
API_CONFIGS = [
    {
        "url": "https://alfa-leetcode-api.onrender.com/{username}/acSubmission",
        "response_handler": lambda data: filter_by_today(data.get("submission", [])),
    },
    {
        "url": "https://leetcode-api-faisalshohag.vercel.app/{username}",
        "response_handler": lambda data: filter_by_accepted_and_today(data.get("recentSubmissions", [])),
    },
]

def is_today(timestamp):
    """Check if the submission was made today."""
    return datetime.fromtimestamp(int(timestamp), tz=timezone.utc).date() == datetime.now(timezone.utc).date()

def filter_by_accepted_and_today(submissions):
    """
    Filter submissions where status is 'accepted' and the timestamp is today (UTC).

    Args:
        submissions (list): List of submission dictionaries.

    Returns:
        list: Filtered submissions meeting both criteria.
    """
    return [
        submission
        for submission in submissions
        if submission.get("statusDisplay") == "Accepted" and
           is_today(submission.get("timestamp", 0))
    ]


def filter_by_today(submissions):
    """
    Filter submissions where the timestamp is today (UTC), ignoring status.

    Args:
        submissions (list): List of submission dictionaries.

    Returns:
        list: Filtered submissions made today.
    """
    return [
        submission
        for submission in submissions
        if is_today(submission.get("timestamp", 0))
    ]


async def fetch_user_submission(session, username):
    """
    Fetch submissions for a user by trying multiple APIs with distinct configurations.

    Args:
        session (aiohttp.ClientSession): The aiohttp session for HTTP requests.
        username (str): LeetCode username.

    Returns:
        dict: A dictionary containing the user's submissions or an error message.
    """
    for api_config in API_CONFIGS:
        url = api_config["url"].format(username=username)
        response_handler = api_config["response_handler"]
        logger.info(f"Trying API: {url}")
        
        retries = 0
        while retries < MAX_RETRIES:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()  # Parse JSON response
                            filtered_submissions = response_handler(data)
                            today_unique_submissions = get_today_unique_submissions(username, filtered_submissions)
                            
                            logger.info(f"Submissions for {username}: {today_unique_submissions}")
                            return today_unique_submissions
                        except Exception as e:
                            logger.error(f"Error processing response from {url}: {str(e)}")
                            break  # Invalid response format, try the next API
                    elif response.status == 429:  # Rate-limited error (too many requests)
                        retry_after = int(response.headers.get("Retry-After", RETRY_DELAY))
                        logger.info(f"Rate limit exceeded for {username}. Retrying after {retry_after} seconds.")
                        time.sleep(retry_after)
                        retries += 1
                    else:
                        logger.info(f"Failed with status {response.status} from {url}")
                        break  # Try the next API

            except Exception as e:
                logger.error(f"Error fetching submissions from {url} for {username}: {str(e)}")
                break  # Error with this API, try the next one

    return {"leetcode_username": username, "error": "All APIs failed to fetch submissions."}


def get_today_unique_submissions(username, submissions):
    """
    Get unique submissions for the current day (UTC) for the given user.

    Args:
        username (str): The LeetCode username.
        submissions (list): List of submissions returned by the API.

    Returns:
        dict: A dictionary containing the username and today's unique submissions (titles only).
    """
    seen_slugs = set()  # To track unique titleSlug values
    today_submissions = []

    for submission in submissions:
        title_slug = submission.get("titleSlug")
        if title_slug not in seen_slugs:
            seen_slugs.add(title_slug)
            today_submissions.append(submission.get("title"))  # Collect only the title

    return {
        "leetcode_username": username,
        "today_submissions": today_submissions
    }


async def fetch_submissions_for_users(user_list):
    """
    Fetch submissions for all users concurrently, trying multiple APIs if necessary.

    Args:
        user_list (list): List of LeetCode usernames.

    Returns:
        list: A list of dictionaries containing each user's unique submissions for today.
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        for user in user_list:
            logger.info(f"Processing submissions for user: {user['leetcode_username']}")
            tasks.append(fetch_user_submission(session, user['leetcode_username']))
        results = await asyncio.gather(*tasks)
        return results
