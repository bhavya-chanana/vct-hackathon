import json
from typing import Dict, List, Any

def load_json(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def create_combined_json():
    players = load_json(r'test-data\players.json')
    teams = load_json(r'test-data\teams.json')
    tournaments = load_json(r'test-data\tournaments.json')
    leagues = load_json(r'test-data\leagues.json')
    mapping_data = load_json(r'test-data\mapping_data.json')

    # Create dictionaries for faster lookup
    teams_dict = {team['id']: team for team in teams}
    tournaments_dict = {t['id']: t for t in tournaments}
    leagues_dict = {l['league_id']: l for l in leagues}

    combined_data = []

    for player in players:
        player_data = {
            "player": player,
            "team": None,
            "tournaments": [],
            "league": None
        }

        # Find team
        if player['home_team_id'] in teams_dict:
            team = teams_dict[player['home_team_id']]
            player_data["team"] = team

            # Find league
            if 'home_league_id' in team and team['home_league_id'] in leagues_dict:
                player_data["league"] = leagues_dict[team['home_league_id']]

        # Find tournaments and additional mappings
        for mapping in mapping_data:
            for participant_id, mapped_player_id in mapping['participantMapping'].items():
                if mapped_player_id == player['id']:
                    if mapping['tournamentId'] in tournaments_dict:
                        tournament = tournaments_dict[mapping['tournamentId']]
                        player_data["tournaments"].append(tournament)
                        
                        # If league not found earlier, try to find it through tournament
                        if not player_data["league"] and 'league_id' in tournament:
                            if tournament['league_id'] in leagues_dict:
                                player_data["league"] = leagues_dict[tournament['league_id']]

        combined_data.append(player_data)

    return combined_data

# Create and save the combined JSON
combined_json = create_combined_json()
with open('combined_data.json', 'w', encoding='utf-8') as outfile:
    json.dump(combined_json, outfile, indent=2, ensure_ascii=False)

print("Combined JSON file has been created as 'combined_data.json'")