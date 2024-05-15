from enum import Enum
import os


class Settings(Enum):

    PATH_GO = absolute_path = os.path.expanduser("~/go/bin")

    VERSION_APP: str = "0.1.0"
    BANNER: str = f"""
                     .|,
     _.  .. .._ _ *  -*-
    (_]\_|(_|[ | )|  '|`
       ._| 

           {VERSION_APP}

"""
