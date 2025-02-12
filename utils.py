import re


def clean_title_remove_brackets(title: str) -> str:
    return re.sub(r"\(.*\)", "", title).strip()
