from datetime import datetime

def ddmmyyyy_to_yyyymmdd(date_str):
    """Convert dd-mm-yyyy to yyyy-mm-dd for DB queries. Returns original if invalid."""
    if date_str and '-' in date_str:
        try:
            return datetime.strptime(date_str, '%d-%m-%Y').strftime('%Y-%m-%d')
        except Exception:
            return date_str
    return date_str

def yyyymmdd_to_ddmmyyyy(date_str):
    """Convert yyyy-mm-dd to dd-mm-yyyy for display. Returns original if invalid."""
    if date_str and '-' in date_str:
        try:
            if date_str.count('-') == 2:
                parts = date_str.split('-')
                if len(parts[0]) == 4:
                    return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d-%m-%Y')
                elif len(parts[2]) == 4:
                    return date_str
        except Exception:
            return date_str
    return date_str or ''