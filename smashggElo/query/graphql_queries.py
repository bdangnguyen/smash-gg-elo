tournament_query = """
query TournamentQuery($slug: String) {
		tournament(slug: $slug){
			events {
				id
				name
			}
		}
	}"""

total_player_page_query = """
query TotalPlayerPage($eventId:ID!){
  event(id:$eventId){
    entrants {
      pageInfo{
        totalPages
      }
    }
  }
}
"""

id_query2 = """
query EventUserId($eventId:ID!, $page:Int) {
  event(id:$eventId) {
    entrants(query: {page: $page}) {
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
total_event_sets_page_query = """
query EventSetsPageTotal($eventId:ID!,$perPage:Int) {
  event(id:$eventId){
    sets(
      perPage: $perPage
      sortType:CALL_ORDER){
      pageInfo {
        totalPages
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