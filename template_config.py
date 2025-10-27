from fastapi.templating import Jinja2Templates
from datetime import datetime

def strftime_filter(date_value, format_string):
    """Custom strftime filter for Jinja2 templates"""
    if isinstance(date_value, (int, float)):
        # Convert timestamp to datetime
        date_value = datetime.fromtimestamp(date_value)
    elif isinstance(date_value, str):
        # Try to parse string as datetime
        try:
            date_value = datetime.fromisoformat(date_value)
        except ValueError:
            return str(date_value)
    elif not isinstance(date_value, datetime):
        return str(date_value)
    
    return date_value.strftime(format_string)

# Helper function for settings
def get_settings_dict():
    """Get settings for templates"""
    try:
        from db_operations import DatabaseOperations
        return DatabaseOperations.get_settings_dict()
    except Exception:
        return {}

# Create templates instance with custom filters
templates = Jinja2Templates(directory="templates")
templates.env.filters["strftime"] = strftime_filter
templates.env.globals["get_settings"] = get_settings_dict