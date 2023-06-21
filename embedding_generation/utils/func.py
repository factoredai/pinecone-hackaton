import re


def remove_html_tags(text):
    """Remove html tags from a string"""
    clean = re.compile('<.*?>')
    
    return re.sub(clean, '', text).strip('\n')


def process_text(text: str) -> str:
    """
    Remove hashtags, twitter handles, newlines and urls,
    then convert text to lowercase and remove trailing and
    leading spaces.

    Args:
        text: a string to process

    Returns:
        processed string
    """

    # Deleting @ character
    text = re.sub(r"@", "", text)

    # Deleting # character
    text = re.sub(r"#", "", text)

    # Deleting \n indicator
    text = re.sub(r"\n", "", text)

    # Removing hyperlinks
    text = re.sub(r"https?://[^\s\n\r]+", "", text)

    # Lower case text
    text = text.lower()

    # remove leading and trailing spaces
    text = text.strip()

    return text