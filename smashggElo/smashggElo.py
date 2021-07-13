import datetime
import math
import json
import requests

from model.base import *
from query.graphql_queries import *

K_FACTOR_PROVISIONAL = 32
K_FACTOR_STANDARD = 24
PROVISIONAL_LIMIT = 20

# Calculate the expected score according to the Elo rating algorithm.
# This should only be called every time we update the match records.
def expected_score(totalGames: int, player_elo: int, opponent_elo: int):
    calculated_score = 0.0
    for i in range(totalGames):
        quotient = (1.0 + math.pow(10,(opponent_elo - player_elo) / 400))
        calculated_score += (1.0 / quotient)
    return calculated_score


# Calculate the changed Elo according to the Elo rating algorithm.
# This should only be called every time we update the match records.
def calculate_elo(prev_elo: int, score: int, ex_score: float, k_factor: int):
    new_elo = round(prev_elo + (k_factor * (score - ex_score)), 0)
    return new_elo


def main():
    # Initialize db
    db.connect()
    db.create_tables([PlayerRecord, MatchRecord])


    auth_token = input("Enter your authorization token: ")
    tournament_id = input("Enter tournament slug: ")

    url = 'https://api.smash.gg/gql/alpha'
    headers = {"Authorization": "Bearer " + auth_token}

    # Request tournament event list.
    r = requests.post(
        url,
        json={
            'query': tournament_query,
            'variables':{'slug': tournament_id}},
        headers=headers) 
    json_data = json.loads(r.text)
    event_list = json_data['data']['tournament']['events']
    event_id = ""

    # Protection against empty tournament case.
    if (len(event_list) == 0):
	    raise Exception("No events were found.")

    # Get the event id. This is the case where we have more than 1 event.
    # O(2n), where n = number of events.
    if (len(event_list) > 1):
	    print("More than one event was detected, input desired event id:")
	    for i in range(len(event_list)):
		    print(event_list[i])
	
	    # Invalid event_id check.
	    event_id = int(input())
	    event_id_bool = False
	    for i in range(len(event_list)):
		    if (event_id == event_list[i].get('id')):
			    event_id_bool = True
	    if (event_id_bool == False):
		    raise Exception("Event id does not correspond with ids found.")
    else:
	    event_id = event_list[0].get('id')

    # Convert to string as GraphQL takes type ID! as a string.
    event_id = str(event_id)

    # Request the list of players attending the tournament with the format 
    # [{'gamerTag': gbl username, 'user': {'id': gbl ID}, 'id' tournament id}]
    request_id2 = requests.post(
        url,
        json={
            'query': id_query2,
            'variables':{'eventId': event_id}},
        headers = headers)
    json_id2_data = json.loads(request_id2.text)

    # Format the obtained list into a dictionary for ease. Keys being the 
    # user ID associated with the tournament. Values being pairs of type 
    # (global username, global ID). O(n), where n = number of players.
    player_dict = {}
    for user in json_id2_data['data']['event']['entrants']['nodes']:
        player_dict[user.get('id')] = (
            user['participants'][0].get('gamerTag'),
            user['participants'][0].get('user').get('id')
        )
    
    # Request all sets completed in desired event.
    request_sets = requests.post(
        url,
        json={
            'query': event_sets_query,
            'variables':{'eventId': event_id, 'page': 1, 'perPage':999}},
        headers = headers)
    json_set_data = json.loads(request_sets.text)
    set_list = json_set_data['data']['event']['sets']['nodes']


    # Get time the set was completed. Get player one's id and score.
    # Get player two's id and score. In the worst case, we have O(23n), where
    # n = the number of matches. We have to update the match record and each
    # player. Practically speaking, this will always be O(9n). We don't usually
    # ever have more than 6 matches in a set.
    for i in range(len(set_list)):
        time_complete = datetime.datetime.utcfromtimestamp(
            set_list[len(set_list) - 1 - i]['completedAt'])

        user_one_tournament_id = set_list[
            len(set_list) - 1 - i][
                'slots'][
                    0].get('entrant').get('id')
        user_one_score = set_list[
            len(set_list) - 1 - i][
                'slots'][
                    0].get('standing').get('stats').get('score').get('value')
        user_one_global_id = player_dict.get(user_one_tournament_id)[1]
        user_one_name = player_dict.get(user_one_tournament_id)[0]
        user_one_record = PlayerRecord.get_or_none(
            PlayerRecord.player_global_id == user_one_global_id)
        if (user_one_record is None):
            user_one_record = PlayerRecord.create(
                player_global_id = user_one_global_id,
                player_name = user_one_name)
        user_one_elo = user_one_record.player_elo
        user_one_provisional_bool = user_one_record.player_is_provisional

        user_two_tournament_id = set_list[
            len(set_list) - 1 - i][
                'slots'][
                    1].get('entrant').get('id')
        user_two_score = set_list[
            len(set_list) - 1 - i][
                'slots'][
                    1].get('standing').get('stats').get('score').get('value')
        user_two_global_id = player_dict.get(user_two_tournament_id)[1]
        user_two_name = player_dict.get(user_two_tournament_id)[0]
        user_two_record = PlayerRecord.get_or_none(
            PlayerRecord.player_global_id == user_two_global_id)
        if (user_two_record is None):
            user_two_record = PlayerRecord.create(
                player_global_id = user_two_global_id,
                player_name = user_two_name)
        user_two_elo = user_two_record.player_elo
        user_two_provisional_bool = user_two_record.player_is_provisional

        # In the event of a DQ, we don't calculate Elo ratings.
        # Update the match records still.
        if (user_one_score == -1 or user_two_score == -1):
            match_record_DQ = MatchRecord.create(
                player_one_global_id = user_one_global_id,
                player_one_name = user_one_name,
                player_one_elo = user_one_elo,
                player_one_score = user_one_score,
                player_one_elo_delta = 0.0,
                player_two_global_id = user_two_global_id,
                player_two_name = user_two_name,
                player_two_elo = user_two_elo,
                player_two_score = user_two_score,
                player_two_elo_delta = 0.0,
                tournament_name = tournament_id,
                set_time = datetime.datetime.strftime(
                    time_complete,
                    "%d/%m/%y %I:%M %S %p")
            )
        else:
            # Calculate the expected score.
            total_games = user_one_score + user_two_score
            player_one_predicted_score = expected_score(
                total_games,
                user_one_elo,
                user_two_elo
            )
            player_two_predicted_score = expected_score(
                total_games,
                user_one_elo,
                user_two_elo
            )

            # Calculate Elo. Change K-factor if they are provisional.
            player_one_new_elo = 0
            player_two_new_elo = 0
            if (user_one_provisional_bool == True):
                player_one_new_elo = calculate_elo(
                    user_one_elo,
                    user_one_score,
                    player_one_predicted_score,
                    k_factor = K_FACTOR_PROVISIONAL
                )
            else:
                player_one_new_elo = calculate_elo(
                    user_one_elo,
                    user_one_score,
                    player_one_predicted_score,
                    k_factor = K_FACTOR_STANDARD
                )
            if (user_two_provisional_bool == True):
                player_two_new_elo = calculate_elo(
                    user_two_elo,
                    user_two_score,
                    player_two_predicted_score,
                    k_factor = K_FACTOR_PROVISIONAL
                )
            else:
                player_two_new_elo = calculate_elo(
                    user_two_elo,
                    user_two_score,
                    player_two_predicted_score,
                    k_factor = K_FACTOR_STANDARD
                )
            
            # Update the match records.
            match_record_DQ = MatchRecord.create(
                player_one_global_id = user_one_global_id,
                player_one_name = user_one_name,
                player_one_elo = user_one_elo,
                player_one_score = user_one_score,
                player_one_elo_delta = player_one_new_elo - user_one_elo,
                player_two_global_id = user_two_global_id,
                player_two_name = user_two_name,
                player_two_elo = user_two_elo,
                player_two_score = user_two_score,
                player_two_elo_delta = player_two_new_elo - user_two_elo,
                tournament_name = tournament_id,
                set_time = datetime.datetime.strftime(
                    time_complete,
                    "%d/%m/%y %I:%M %S %p")
            )

            # Update player1 records.
            user_one_record.player_name = user_one_name
            user_one_record.player_elo = player_one_new_elo
            user_one_record.player_wins += user_one_score
            user_one_record.player_losses += user_two_score
            # The tournament winner match occurs at the end of the call order.
            if (i == (len(set_list) - 1)):
                if (user_one_score > user_two_score):
                    user_one_record.player_tournament_wins += 1
            if (user_one_record.player_wins 
                + user_one_record.player_losses > PROVISIONAL_LIMIT
                and user_one_record.player_is_provisional == True):
                    user_one_record.player_is_provisional = False
            user_one_record.save()

            # Update player2 records.
            user_two_record.player_name = user_two_name
            user_two_record.player_elo = player_two_new_elo
            user_two_record.player_wins += user_two_score
            user_two_record.player_losses += user_one_score
            # The tournament winner match occurs at the end of the call order.
            if (i == (len(set_list) - 1)):
                if (user_two_score > user_one_score):
                    user_two_record.player_tournament_wins += 1
            if (user_two_record.player_wins 
                + user_two_record.player_losses > PROVISIONAL_LIMIT
                and user_two_record.player_is_provisional == True):
                    user_two_record.player_is_provisional = False
            user_two_record.save()
    
    # Assign ranking according to Elo rating now that we are done calculating.
    cursor = db.execute_sql(
        'SELECT player_global_id ' +
        'FROM playerrecord ' +
        'ORDER BY player_elo DESC')
    count = 1
    for row in cursor.fetchall():
        db.execute_sql(
            'UPDATE playerrecord ' +
            'SET player_rank = ' + str(count) +
            ' WHERE player_global_id = ' + str(row[0])
        )
        count += 1

    # Cleanup.
    db.close()

if __name__ == "__main__":
    main()