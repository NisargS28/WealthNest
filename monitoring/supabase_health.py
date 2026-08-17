import os
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]


def check_database():
    url = f"{SUPABASE_URL}/rest/v1/users?select=id&limit=1"

    request = Request(
        url,
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        },
        method="GET",
    )

    start = time.perf_counter()

    try:
        with urlopen(request, timeout=20) as response:
            elapsed = (time.perf_counter() - start) * 1000

            print("Supabase: ONLINE")
            print(f"HTTP status: {response.status}")
            print(f"Response time: {elapsed:.2f} ms")

            return True

    except HTTPError as e:
        print(f"Supabase HTTP error: {e.code}")
        return False

    except URLError as e:
        print(f"Supabase connection error: {e.reason}")
        return False

    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = check_database()

    if not success:
        sys.exit(1)