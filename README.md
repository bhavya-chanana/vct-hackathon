# VALORANT Esports Team Creator and Comparison App

This project provides a comprehensive tool for managing and creating VALORANT esports teams. Built with Streamlit and powered by AWS Bedrock, it allows team managers to create teams, compare players from different leagues, and even query a chatbot to get tailored team suggestions based on an extensive knowledge base.
YouTube demo - [VALORANT Esports Team Creator](https://www.youtube.com/watch?v=ig6K2p5thWg)

## Features

1. **Chatbot for Team Suggestions**: Ask the chatbot for tailored team compositions based on your needs and knowledge of VALORANT players.
2. **Player Comparison**: Compare players from the same league. The app supports comparisons across three leagues:
   - VCT
   - Game Changers
   - Challengers
3. **Team Creation**: Select 5 players, assign roles, and add custom notes to create your own team.
4. **View Teams**: Review created teams and ask questions about them by querying the knowledge base.

---

## Data Scraping

We scraped data from multiple sources, including `vlr.gg` over several hours, but discovered some issues during the process. For example:

- **Misleading Agent Stats**: The agent information for certain players on `vlr.gg` was found to be inaccurate. For instance, TenZ, a well-known player, is frequently listed as playing Sage, though he rarely picks Sage in competitive matches.
  
We ultimately found that scraping from `vlr.gg` wasn’t ideal for reliable agent-specific stats, which led to a significant portion of our data cleaning and verification process.

### Example of Inaccuracy on vlr.gg:
- The URL we used for player statistics: [https://www.vlr.gg/stats](https://www.vlr.gg/stats)
- Player profile URL example: [https://www.vlr.gg/player/9/tenz](https://www.vlr.gg/player/9/tenz)

Automating this process was challenging since we had to go through every player's profile individually to extract accurate stats. We initially tried using Liquipedia, but it had fewer players, so we shifted to automating scraping from vlr.gg.

One of the key challenges was that player pages on vlr.gg were not easily accessible by just replacing the name of the player in the URL. Instead, each player had a unique ID associated with their profile. For example, TenZ’s profile page URL is:

Here, the number `9` is the unique ID for TenZ, which meant we had to automate the process of searching for the player profile and extracting this ID for every player to scrape their detailed stats. This added a layer of complexity to our data scraping process.
- Player profile URL we used for vlr example: [https://www.vlr.gg/player/9/tenz/?timespan=all](https://www.vlr.gg/player/9/tenz/?timespan=all)
This made scraping detailed and accurate stats for each player more complex, as the process couldn’t be achieved by just replacing the player’s name in the URL, you can remove the player name from the below URL, it's going to behave the same
https://www.vlr.gg/player/{player_id}/{player_name}/?timespan=all
---

## Final Data CSV

After extensive data scraping and cleaning, we compiled a final CSV dataset containing detailed statistics for players across various leagues. The dataset includes key performance metrics as well as metadata on the players' organizations and agents. The columns in the final dataset are:

| Column Name                        | Description                                                                 |
|-------------------------------------|-----------------------------------------------------------------------------|
| **handle**                          | Player's in-game name or handle                                             |
| **first_name**                      | Player's first name                                                         |
| **last_name**                       | Player's last name                                                          |
| **status**                          | Player's current status (active, retired, etc.)                             |
| **photo_url**                       | URL to the player's photo                                                   |
| **org**                             | Organization the player belongs to                                          |
| **agents**                          | Agents frequently used by the player                                        |
| **rounds_played**                   | Total number of rounds the player has played                                |
| **rating**                          | Player's rating based on performance metrics                                |
| **average_combat_score**            | Player's average combat score (ACS)                                         |
| **kill_deaths**                     | Kill-to-death ratio                                                         |
| **kill_assists_survived_traded**     | Combined metric tracking kills, assists, survivals, and trade kills         |
| **average_damage_per_round**        | Average damage the player deals per round                                   |
| **kills_per_round**                 | Average number of kills per round                                           |
| **assists_per_round**               | Average number of assists per round                                         |
| **first_kills_per_round**           | Average number of first kills per round                                     |
| **first_deaths_per_round**          | Average number of first deaths per round                                    |
| **headshot_percentage**             | Percentage of the player's kills that are headshots                         |
| **clutch_success_percentage**       | Player's success rate in clutch situations                                  |
| **igl**                             | Whether the player is an in-game leader (IGL)                               |
| **gender**                          | Player's gender                                                             |
| **country**                         | Country the player represents                                               |
| **primary_language**                | Player's primary language, (secondary language)                                                  |
| **regions**                         | Regions the player competes in (e.g., NA, EU, SA)                          |
| **league**                          | The league the player competes in (VCT, Game Changers, Challengers)         |

---

## How to Run the Project

1. Clone the repository:
    ```bash
    git clone https://github.com/your-repo-url.git
    ```
   
2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Add your AWS credentials to the `.env` file or configure them through the AWS CLI.

4. Run the Streamlit application:
    ```bash
    streamlit run app.py
    ```

---

## Conclusion

This app is a powerful tool for VALORANT team managers to create, manage, and compare players from different leagues. With the integration of AWS Bedrock and accurate, cleaned data, team managers can make more informed decisions for their rosters.
