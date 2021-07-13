tournament_query = """
query TournamentQuery($slug: String) {
		tournament(slug: $slug){
			events {
				id
				name
			}
		}
	}"""

id_query = """
query IDQuery($slug:String!, $page:Int){
  tournament(slug:$slug) {
    participants(query:
    {page:$page}
    ) {
      nodes {
        gamerTag
        user {
          id
        }
        id
      }
    }
  }
}
"""

id_query2 = """
query EventUserId($eventId:ID!) {
  event(id:$eventId) {
    entrants {
      nodes {
        id
        participants {
          gamerTag
          user {
            id
          }
        }
      }
    }
  }
}
"""

event_sets_query = """
query EventSetsCustom($eventId:ID!, $page:Int, $perPage:Int) {
  event(id:$eventId) {
    sets(
      page: $page
      perPage: $perPage
      sortType:CALL_ORDER) {
      pageInfo {
        totalPages
        total
      }
      nodes {
        completedAt
        slots {
          entrant {
            id
          }
          standing {
            stats {
              score {
                value
              }
            }
          }
        }
      }
    }
  }
}
"""