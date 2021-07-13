from peewee import *

db = SqliteDatabase('.\smashggElo.db') 

# Contains the overarching info of an individual player.
class PlayerRecord(Model):
    player_global_id = IntegerField(primary_key=True)
    player_name = TextField()
    player_elo = IntegerField(default=1500)
    player_rank = IntegerField(default=0)
    player_wins = IntegerField(default=0)
    player_losses = IntegerField(default=0)
    player_tournament_wins = IntegerField(default=0)
    player_is_provisional = BooleanField(default=True)

    class Meta:
        database = db

# Contains all of the matches ever recorded by the program.
class MatchRecord(Model):
    player_one_global_id = IntegerField()
    player_one_name = TextField()
    player_one_elo = IntegerField()
    player_one_score = IntegerField()
    player_one_elo_delta = IntegerField()
    player_two_global_id = IntegerField()
    player_two_name = TextField()
    player_two_elo = IntegerField()
    player_two_score = IntegerField()
    player_two_elo_delta = IntegerField()
    tournament_name = TextField()
    set_time = TextField()

    class Meta:
        database = db