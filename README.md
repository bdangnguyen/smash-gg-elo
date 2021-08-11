A python program to query https://smash.gg for all match data in an event and scrubs through it to obtain players and calculating their elo rating. Match history and relevant
player data are stored in a local sqlite database.

# Requirements
* The tournament and its slug to parse data from
* A smash.gg API authentication token

# Dependencies
* peewee
* requests

# Usage
```
python3 smashggElo.py
```

# Elo Info
Below is a general list of particular choices regarding the Elo rating algorithm.
## Starting Rating
All players are automatically assigned an intial provisional rating of 1500. For them to leave provisional status, they must have in total at least more than 20 recorded games
in their record.
## K-factor
Provisional ratings have a K-factor of 32. Once they leave that status, the K-factor is adjusted to 24. The provisional K-factor encourages volatility in their rating and quick
adjustment for both strong and weaker players. We assume no smaller K-factor due to the lifetime of a tournament circuit being much smaller than a lifetime rating organization
such as FIDE.

# Todo
* Add useful statistics queries to sqlite database.
