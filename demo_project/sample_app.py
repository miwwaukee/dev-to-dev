"""
Sample application for testing DevHelper MCP Server.
Contains various tech debt markers for demonstration.
"""

# TODO: Add proper error handling - low priority
def legacy_handler(data):
    return data


# FIXME: handle token expiration - critical for auth!
def refresh_token(token):
    # BUG: This doesn't actually refresh the token
    return token


# HACK: temporary workaround for API rate limit
def fetch_data(url):
    import time
    time.sleep(1)  # XXX: This is inefficient
    return {"data": "mock"}


# TODO: refactor this function for better performance
def process_items(items):
    result = []
    for item in items:
        # FIXME: memory leak - items not cleaned up
        result.append(item)
    return result


# SECURITY: need to add input validation
def user_input_handler(user_input):
    # BUG: SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return query


# TODO: Add unit tests - someday
def calculate_total(prices):
    return sum(prices)


# LATER: optimize this for large datasets
def sort_data(data):
    return sorted(data)
