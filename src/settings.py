from pydantic import BaseSettings


class Settings(BaseSettings):

    VERSION_APP: str = "0.1.0"
    BANNER: str = f"""

                 .|,
 _.  .. .._ _ *  -*-
(_]\_|(_|[ | )|  '|`
   ._| 

    {VERSION_APP}
"""
