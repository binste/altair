"""
Binned Scatter Plot
------------------
This example shows how to make a binned scatter plot.
"""
# category: distributions
import altair as alt
from vega_datasets import data

source = data.movies.url

alt.Chart(source).mark_circle().encode(
    alt.X('IMDB_Rating:Q', bin=True),
    alt.Y('Rotten_Tomatoes_Rating:Q', bin=True),
    size='count()'
)
