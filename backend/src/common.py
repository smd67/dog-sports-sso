import os
from typing import Union


def get_secret(key: str) -> Union[str, None]:
    """
    Glue code to integrate with docker compose secrets.

    Parameters
    ----------
    key : str
        Environmental variable pointing to secret file

    Returns
    -------
    Union[str, None]
        Return secret value.
    """
    # Check for _FILE suffix first
    file_env = f"{key}_FILE"
    if file_env in os.environ:
        with open(os.environ[file_env], "r") as f:
            return f.read().strip()
    # Fall back to environment variable
    return os.environ.get(key)
