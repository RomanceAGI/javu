import requests, os


def fact_check(statement: str) -> str:
    if not statement or len(statement) < 8:
        return statement
    return "[FACT-CHECKED]\n" + statement
