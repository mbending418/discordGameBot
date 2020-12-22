import numpy as np
import imageio  
import os

from ..common import GameClasses
from ..common import GameExceptions

CURRENT_BOARD_IMAGE = "current_board.jpg"

def merge_image_files(image_files, output_file):

    images = [imageio.imread(f) for f in image_files]
    
    output_image = np.concatenate(images, axis=1)
    
    imageio.imsave(output_file, output_image)
    
def cut_image_file(image_file, cuts, output_file_base="output.jpg"):
    
    output_file_name, output_file_ext = os.path.splitext(output_file_base)
    
    image = imageio.imread(image_file)
    
    left_cut = [0] + cuts
    right_cut = cuts + [image.shape[1]]
    
    images = [image[:, start:finish, :] for start, finish in zip(left_cut, right_cut)]
    
    [imageio.imsave(f"{output_file_name}_{i}.{output_file_ext}", img) for i, img in enumerate(images)]
    
def create_board(temp_directory, base_directory, player_count, mission_results):

    board_directory = os.path.join(base_directory, "boards", f"{player_count}_players")
    
    board_file = os.path.join(temp_directory,CURRENT_BOARD_IMAGE)
    
    if os.path.isfile(board_file):
        os.remove(board_file)
    
    if os.path.isdir(board_directory):
    
        files = [os.path.join(board_directory, f"game_board_{player_count}_{i}_{result}.jpg") for i, result in enumerate(mission_results)]
    
        merge_image_files(files, board_file)
        
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
    
    def __init__(self, player_count, temp_dir, avalon_resources_folder):
    
        if player_count not in self._mission_counts:
            raise GameExceptions.DiscordGameIllegalMove(f"Cannot Start Game with '{player_count}' players")
        
        self.player_count = player_count
        self.temp_dir = temp_dir
        self.avalon_resources_folder = avalon_resources_folder
        
        self.vote_track = 1
        self.current_mission = 0
        self.failed_mission_count = 0
        self.passed_mission_count = 0
        
        self.mission_log = ["================================"]
        self.vote_log = ["================================"]
        
        self.results = [self._current_token] + [self._empty_token for m in range(0, len(self.get_mission_counts()) - 1)]
        
        self.render_board()
    
    def generate_board(self, channel = None):
    
        main_text = "\n".join(self.generate_mission_info())
        main_image = os.path.join(self.temp_dir, CURRENT_BOARD_IMAGE)
    
        if os.path.isfile(main_image):
            main_board = GameClasses.CommandResultMessage(text=main_text, image=main_image, send_both=True, destination = channel)
        else:
            main_board = GameClasses.CommandResultMessage(text=main_text, destination = channel)
        
        sub_board_info = [
            "Vote Track: " + str(self.vote_track),
            "Player Count: " + str(self.player_count),
            "Number of Evil Players: " + str(self.get_team_evil_count())]
        
        sub_board = GameClasses.CommandResultMessage(text="\n".join(sub_board_info), destination = channel)
        
        return [main_board, sub_board]
    
    def render_board(self):
    
        translation_dict = {
            self._pass_token : "pass",
            self._fail_token : "fail",
            self._current_token : "blank",
            self._empty_token : "blank"
        }
    
        mission_results = [translation_dict[r] for r in self.results]
        
        create_board(self.temp_dir, self.avalon_resources_folder, self.player_count, mission_results)
        
    def generate_mission_info(self):
        return [f"Mission #{m+1} | player_count = {count} | Fails required: {self.number_fails_required(m)} | {self.results[m]}" for m, count in enumerate(self.get_mission_counts())]
    
    def advance_vote_track(self):
        self.vote_track += 1
    
    def reset_vote_track(self):
        self.vote_track = 1
        
    def get_team_evil_count(self):
        return self._team_evil_counts[self.player_count]
        
    def get_mission_counts(self):
        return self._mission_counts[self.player_count]
        
    def get_current_mission_count(self):
        return self._mission_counts[self.player_count][self.current_mission]
        
    def number_fails_required(self, mission_number):
        if mission_number == 3 and self.player_count >= 7:
            return 2
        else:
            return 1
        
    def set_mission_results(self, mission, results):
        self.results[mission] = results
        
    def create_mission_reveal(self, temp_directory, mission_cards, file_name = "current_mission.jpg"):

        other_directory = os.path.join(self.avalon_resources_folder, "other")
    
        mission_card_file = os.path.join(temp_directory, file_name)
    
        if os.path.isfile(mission_card_file):
            os.remove(mission_card_file)
        
        files = [os.path.join(other_directory, f"{card}.jpg") for card in mission_cards]
        merge_image_files(files, mission_card_file)