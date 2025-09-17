import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime


class LichessData:

    def __init__(self,username="Fearghal97",number_of_games=0,gamemode="all",opening="",personal_token=""):
        self.error_message=None
        self.USERNAME = username
        self.number_of_games = number_of_games
        self.gamemode=gamemode
        if len(opening)>0:
            self.opening_list=opening.split(',')
        else:
            self.opening_list=[]
        #self.opening=opening
        self.url = f"https://lichess.org/api/games/user/{self.USERNAME}"
        self.personal_token=personal_token
        self.headers = {
            "Authorization": f"Bearer {self.personal_token}",
            "Accept": "application/x-ndjson"
        }

        self.params = {
            "max": self.number_of_games,         # number of games to fetch
            "perfType": self.gamemode,  
            "moves": True,      # include moves
            "pgnInJson": True,  # return PGN in JSON format
            "opening": True
        }

        self.records=[]

    def get_games_from_lichess(self):
        self.games=[]
        try:
            with requests.get(self.url, headers=self.headers, params=self.params) as r:
                r.raise_for_status()
                for line in r.iter_lines(decode_unicode=True):
                    if not line:              # skip keep-alives/blank lines
                        continue
                    try:
                        self.games.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print("Bad line:", line[:200], e)

            #print(len(self.games), "games loaded")
            #print(self.games[0].keys()) # games is a list of dictionaries with keys and values
        except requests.exceptions.HTTPError as http_err:
            print(f"Lichess returned an error: {http_err}")
            self.error_message = str(http_err)
        except requests.exceptions.RequestException as e:
            self.error_message = str(e)

        return self.games

    def create_lichess_dataframe(self,records):
        for g in self.games: # g is an isolated dictionary
            rating_difference=0
            winner='lose'
            try:
                converted_date=datetime.fromtimestamp(g['createdAt'] / 1000)
                date=converted_date.date()
                if g['players']['white']['user']['name'] == self.USERNAME:
                    
                    rating_difference=g['players']['white']['rating']-g['players']['black']['rating']
                    white_player=self.USERNAME
                    black_player=g['players']['black']['user']['name']
                    #print (g.keys())
                    try:
                        if g['winner']=='white':
                            winner='win'
                            winning_colour='white'
                    except:
                        if g['status']=='draw':
                            winner='draw'
                        winning_colour='N/A'
                else:
                    white_player=g['players']['white']['user']['name']
                    black_player=self.USERNAME
                    try:
                        if g['winner']=='black':
                            winner='win'
                            winning_colour='black'
                    except:
                        if g['status']=='draw':
                            winner='draw'
                        winning_colour='N/A'

                    rating_difference=g['players']['black']['rating']-g['players']['white']['rating']

                record={'id':g['id'],
                    'rated':g['rated'],
                    'variant':g['variant'],
                    'game_mode':g['speed'],
                    'perf':g['perf'],
                    'date_played':date,
                    'winner':winning_colour,
                    'white_player':white_player,
                    'black_player':black_player,
                    'won_by_me': winner,
                    'white_rating':g['players']['white']['rating'],
                    'black_rating':g['players']['black']['rating'],
                    'rating_diff':rating_difference,
                    'result':g['status'],
                    'moves':g['moves'],
                    'time_format':g['clock']['initial'],
                    'increment':g['clock']['increment'],
                    'opening':g['opening']['name']

                    }
            
                #if g['game_mode'] == 'blitz':
                    #blitz_records.append(record)
                #if g['game_mode'] == 'bullet':
                    #bullet_records.append(record)
                #print (record)
                self.records.append(record)
            except:
                pass
                #print(g)

        '''
        blitz_df=pd.DataFrame(blitz_records)
        bullet_df=pd.DataFrame(bullet_records)
        bullet_df=bullet_df.sort_values(by="opening")
        '''

        self.lichess_df=pd.DataFrame(self.records)

        return self.lichess_df

    def games_as_colour(self,colour='white'):
        games_by_colour_df = self.lichess_df[self.lichess_df[colour+'_player']==self.USERNAME]
        group_games_by_colour_df=games_by_colour_df.groupby(['grouped_opening','game_mode']).size().reset_index(name=colour+'_total')
        self.lichess_df=self.lichess_df.merge(group_games_by_colour_df,on=['grouped_opening','game_mode'],how='left')

        return self.lichess_df

    def wins_as_colour(self,colour='white'):
        colour_wins_df = self.lichess_df[(self.lichess_df[colour+'_player']==self.USERNAME) & (self.lichess_df['won_by_me']=='win')]
        grouped_by_colour_wins_df = colour_wins_df.groupby(['grouped_opening','game_mode']).size().reset_index(name=colour+'_win')
        self.lichess_df = self.lichess_df.merge(grouped_by_colour_wins_df,on=['grouped_opening','game_mode'],how='left')

        return self.lichess_df

    def win_percentages_by_colour(self,colour=''):
        self.lichess_df[colour+'win_percentage']=round((self.lichess_df[colour+'win']/self.lichess_df[colour+'total'])*100,2)

    def fill_na_on_dfs(self,to_clean_df):
        to_clean_df.fillna(0, inplace=True)

    def group_games_by_opening(self):
        self.lichess_df["grouped_opening"] = self.lichess_df["opening"].str.split(":").str[0].str.strip() # One Method #.str.split().str[:2] experiment with first 2 words only

        #This line groups by the headers, size will count the number of rows present in each group - i.e 2 sicilian defences - 
        #unstack pivots the last index, won_by_me, so it will return draw, lose, win columns with counts filled in for each opening
        #results_df = lichess_df.groupby(["grouped_opening","game_mode", "white_player","black_player","won_by_me"]).size().unstack(fill_value=0)
        grouped_results_df = self.lichess_df.groupby(["grouped_opening","game_mode","won_by_me"]).size().unstack(fill_value=0)

        #This then sums the true false columns, with axis=1 ensuring sum across columns, to give a total games played per opening
        grouped_results_df['total']=grouped_results_df.sum(axis=1)

        #Merges our group back into original dataframe with draw,win,lose,total columns
        self.lichess_df=self.lichess_df.merge(grouped_results_df,on=["grouped_opening","game_mode"],how='left')

        return self.lichess_df

    def filter_by_dates(self,date_as_string=''): # format dd-mm-yyyy
        if date_as_string!='':
            date_as_date = datetime.strptime(date_as_string, "%d-%m-%Y")
            #converted_date=datetime.fromtimestamp(g['createdAt'] / 1000)
            #date=converted_date.date()
            self.lichess_df['date_played'] = pd.to_datetime(self.lichess_df['date_played'])
            self.lichess_df=self.lichess_df[self.lichess_df['date_played']>=date_as_date]

        self.lichess_df['date_played']=self.lichess_df['date_played'].dt.strftime("%d-%m-%Y")
        return self.lichess_df

    def result_breakdown(self):
        self.lost_games_df=self.lichess_df[self.lichess_df['won_by_me']=='lose']
        self.won_games_df=self.lichess_df[self.lichess_df['won_by_me']=='win']
        self.lost_on_time_df=self.lost_games_df[self.lost_games_df['result']=='outoftime']
        percentage_of_games_lost_on_time = (len(self.lost_on_time_df)/len(self.lost_games_df)) * 100
        self.won_on_time_df=self.won_games_df[self.won_games_df['result']=='outoftime']
        percentage_of_games_won_on_time = (len(self.won_on_time_df)/len(self.won_games_df)) * 100

        self.mate_df=self.lost_games_df[self.lost_games_df['result']=='mate']
        percentage_of_games_lost_by_mate = (len(self.mate_df)/len(self.lost_games_df)) * 100

        self.resign_df=self.lost_games_df[self.lost_games_df['result']=='resign']
        percentage_of_games_lost_by_resignation = (len(self.resign_df)/len(self.lost_games_df)) * 100

        result_breakdown_dict = {
            'percentage_of_games_lost_on_time':round(percentage_of_games_lost_on_time,2),
            'percentage_of_games_won_on_time':round(percentage_of_games_won_on_time,2),
            #'percentage_of_games_lost_by_mate':round(percentage_of_games_lost_by_mate,2),
            #'percentage_of_games_lost_by_resignation':round(percentage_of_games_lost_by_resignation,2)
        }
        return result_breakdown_dict

    def filter_data_by_user_input(self):
        if self.gamemode!="all":
            self.lichess_df=self.lichess_df[self.lichess_df['game_mode']==self.gamemode]
        #if self.opening!='' and self.opening in self.lichess_df['grouped_opening'].values:
        #    self.lichess_df= self.lichess_df[self.lichess_df['grouped_opening']==self.opening]
        if len(self.opening_list)>0:
            self.lichess_df = self.lichess_df[self.lichess_df["grouped_opening"].isin(self.opening_list)]

        return self.lichess_df

    def get_opening_success_data(self):
        self.lichess_df=self.lichess_df.sort_values(by=['game_mode','total','win_percentage'],ascending=False).reset_index(drop=True)
        self.result_breakdown_dict=self.result_breakdown()
        self.total_results_df=self.lichess_df[["grouped_opening","game_mode","win","draw","lose","total","white_win","black_win","white_win_percentage","black_win_percentage","win_percentage"]]
        self.total_results_df = self.total_results_df.drop_duplicates(keep='first') # Maybe not the best way but it gives us one result per opening?
        return self.lichess_df,self.total_results_df, self.result_breakdown_dict

    def get_total_data(self,result_breakdown_dict={}):
        total_no_of_games=self.total_results_df['total'].sum()
        total_no_of_white_wins=self.total_results_df['white_win'].sum()
        total_no_of_black_wins=self.total_results_df['black_win'].sum()
        total_no_of_wins=self.total_results_df['win'].sum()
        total_no_of_draws=self.total_results_df['draw'].sum()
        total_no_of_losses=self.total_results_df['lose'].sum()
        white_as_percentage_of_wins = round((total_no_of_white_wins/total_no_of_wins)*100,2)
        black_as_percentage_of_wins = round((total_no_of_black_wins/total_no_of_wins)*100,2)
        white_as_percentage_of_total = round((total_no_of_white_wins/total_no_of_games)*100,2)
        black_as_percentage_of_total = round((total_no_of_black_wins/total_no_of_games)*100,2)

        record={'total_games':[total_no_of_games],
                'total_wins':[total_no_of_wins],
                'total_white_wins':[int(total_no_of_white_wins)],
                'total_black_wins':[int(total_no_of_black_wins)],
                'total_draws':[total_no_of_draws],
                'total_losses':[total_no_of_losses],
                'white_as_percentage_of_wins':[white_as_percentage_of_wins],
                'black_as_percentage_of_wins':[black_as_percentage_of_wins],
                'white_as_percentage_of_total':[white_as_percentage_of_total],
                'black_as_percentage_of_total': [black_as_percentage_of_total],
                }
        
        record.update(result_breakdown_dict)

        self.total_df=pd.DataFrame(record)
        return self.total_df

    def produce_csvs(self,file_path,csv_df):
        csv_df.to_csv(file_path,index=False)

    def run_everything(self,debug=True):
        self.games=self.get_games_from_lichess()
        self.lichess_df=self.create_lichess_dataframe(self.records)
        self.lichess_df=self.group_games_by_opening()
        self.lichess_df=self.filter_data_by_user_input()
        self.games_as_colour(colour='white')
        self.games_as_colour(colour='black')
        self.wins_as_colour(colour='white')
        self.wins_as_colour(colour='black')
        self.win_percentages_by_colour(colour='white_')
        self.win_percentages_by_colour(colour='black_')
        self.win_percentages_by_colour(colour='')
        self.fill_na_on_dfs(self.lichess_df)
        #self.lichess_df=self.filter_by_dates(date_as_string='01-01-2025') # filter by dates not working yet
        self.lichess_df,self.total_results_df,self.result_breakdown_dict=self.get_opening_success_data()
        self.total_df=self.get_total_data(self.result_breakdown_dict)

        if debug==False:
            self.produce_csvs("lichess_data/lichess_games.csv",self.lichess_df)
            self.produce_csvs("lichess_data/opening_success.csv",self.total_results_df)
            self.produce_csvs("lichess_data/total_data_count.csv",self.total_df)
        
        return self.total_df, self.lichess_df, self.total_results_df
#want to create a pandas dataframe with these values
#blitz_records=[]
#bullet_records=[]

#lichess_data=LichessData()
#lichess_data.run_everything()