# pasig-full-disclosure-api
A free-to-use API to get data on Pasig City's ordinances, resolutions, etc.

# TO DO:
- use async and depends
- if start_year > end_year, then the index should be -1; if end_year is None but start_year is not, end_year = start_year and vice-versa; if both are none, returns everything
- better to use li instead of tr to make it more general (includes other notices; doesn't require filtering a-href tags)
- separate function for bids-and-awards, separate function to handle all of eo, ordinances, and resolutions