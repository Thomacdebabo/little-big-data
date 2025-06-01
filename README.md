# little-big-data
Instead of having just a small set of data from many different people we could have a large set for a single person. Sourced from all sorts of sources.
# Goal
Having a framework to deal with data from a wide set of sources. The core things to focus on:
- **Data structure:** How do I store the data efficiently and in a way that makes it easily accessible for further analysis
- **Fast Integration:** Able to integrate new services fast and in a way that it is useful
- **Visualization:** Should be interactive and intuitive to look at

# Tech Stack
# Backend
- use python + uv
- lets use pydantic for the data modeling
- pandas could be also practical for tabular data
- we should abstract the data storage so we can use sql database or json or wathever and load everything

# Frontend
- webbased
- for now just use python fastapi
- some interactive webframework which allows plotting and maybe also 3d things for the future?


# First goal
- be able to fetch data from strava, save it locally and load it
- able to visualize it, I am mainly interested in a timeline
