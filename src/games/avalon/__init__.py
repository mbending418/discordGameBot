class GameBoard():
    
    _team_evil_counts = {
        5 : 2,
        6 : 2,
        7 : 3, 
        8 : 3,
        9 : 3,
        10: 4
    }
    
    _mission_counts = {
        5 : [2, 3, 2, 3, 3],
        6 : [2, 3, 4, 3, 4],
        7 : [2, 3, 3, 4, 4],
        8 : [3, 4, 4, 5, 5],
        9 : [3, 4, 4, 5, 5],
        10: [3, 4, 4, 5, 5]
    }
    
    _pass_token = "PASS!"
    _fail_token = "FAIL!"
    _current_token = "current mission"
    _empty_token = ""
    
    def __init__(self, player_count, temp_dir):
    
        if player_count not in self._mission_counts:
            raise DiscordGameIllegalMove(f"Cannot Start Game with '{player_count}' players")
        
        self._player_count = player_count
        self._temp_dir = temp_dir
        
        self._vote_track = 1
        self._current_mission = 0
        self._failed_mission_count = 0
        self._passed_mission_count = 0
        
        self._mission_log = ["================================"]
        self._vote_log = ["================================"]
        
        self._results = [self._current_token] + [self._empty_token for m in range(0, len(self.get_mission_counts()) - 1)]
        
        self.render_board()
    
    def generate_board(self, channel = None):
    
        main_text = "\n".join(self.generate_mission_info())
        main_image = os.path.join(self._temp_dir, CURRENT_BOARD_IMAGE)
    
        if os.path.isfile(main_image):
            main_board = CommandResultMessage(text=main_text, image=main_image, send_both=True, destination = channel)
        else:
            main_board = CommandResultMessage(text=main_text, destination = channel)
        
        sub_board_info = [
            "Vote Track: " + str(self._vote_track),
            "Player Count: " + str(self._player_count),
            "Number of Evil Players: " + str(self.get_team_evil_count())]
        
        sub_board = CommandResultMessage(text="\n".join(sub_board_info), destination = channel)
        
        return [main_board, sub_board]
    
    def render_board(self):
    
        translation_dict = {
            self._pass_token : "pass",
            self._fail_token : "fail",
            self._current_token : "blank",
            self._empty_token : "blank"
        }
    
        mission_results = [translation_dict[r] for r in self._results]
        
        create_board(self._temp_dir, AVALON_FOLDER, self._player_count, mission_results)
        
    def generate_mission_info(self):
        return [f"Mission #{m+1} | player_count = {count} | Fails required: {self.number_fails_required(m)} | {self._results[m]}" for m, count in enumerate(self.get_mission_counts())]
    
    def advance_vote_track(self):
        self._vote_track += 1
    
    def reset_vote_track(self):
        self._vote_track = 1
        
    def get_team_evil_count(self):
        return self._team_evil_counts[self._player_count]
        
    def get_mission_counts(self):
        return self._mission_counts[self._player_count]
        
    def get_current_mission_count(self):
        return self._mission_counts[self._player_count][self._current_mission]
        
    def number_fails_required(self, mission_number):
        if mission_number == 3 and self._player_count >= 7:
            return 2
        else:
            return 1
        
    def set_mission_results(self, mission, results):
        self._results[mission] = results