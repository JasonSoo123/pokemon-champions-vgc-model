import asyncio
import os
import json
import random
from poke_env.player import Player, RandomPlayer
from poke_env.player.battle_order import DoubleBattleOrder, PassBattleOrder

EX_VGC_TEAM = '''
Incineroar @ Sitrus Berry  
Ability: Intimidate  
Level: 50  
EVs: 32 HP / 32 Atk / 2 SpD  
Adamant Nature  
- Darkest Lariat  
- Parting Shot
- Flare Blitz 
- Fake Out 

Blastoise @ Blastoisinite  
Ability: Torrent  
Level: 50  
EVs: 32 HP / 32 SpA / 2 Spe  
Modest Nature  
- Aura Sphere  
- Dark Pulse  
- Water Spout  
- Fake Out   

Basculegion (M) @ Focus Sash  
Ability: Adaptability  
Level: 50  
EVs: 32 HP / 32 Atk / 2 SpA  
Lonely Nature  
- Aqua Jet  
- Crunch  
- Flip Turn  
- Hydro Pump  

Kingambit @ Black Glasses  
Ability: Defiant  
Level: 50  
EVs: 32 HP / 2 Atk / 32 SpA  
Quiet Nature  
- Brick Break  
- Dark Pulse  
- Foul Play  
- Focus Blast  

Glimmora @ Leftovers  
Ability: Toxic Debris  
Level: 50  
EVs: 2 HP / 32 SpA / 32 Spe  
Timid Nature  
- Acid Armor  
- Dazzling Gleam  
- Earth Power  
- Energy Ball  

Aegislash @ Metal Coat  
Ability: Stance Change  
Level: 50  
EVs: 32 HP / 32 Atk / 2 SpD  
Adamant Nature  
- Shadow Sneak  
- King's Shield  
- Iron Head  
- Swords Dance

'''
# ------------------------ Opening stats json for info ----------------------- #
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
with open(DIRECTORY + '/champions-vgc-stats.json', 'r') as file:
    raw_vgc_data = json.load(file)
    POKEMON_VGC_DATA = raw_vgc_data.get('pokemon', raw_vgc_data)


fakeout_pokemon = []
tailwind_pokemon = []
trickroom_pokemon = []
# -------------------------- getting fakeout_pokemon ------------------------- #
for pokemon_name, data in POKEMON_VGC_DATA.items():
    
    moves = data.get("Moves", {})
    
    if "fakeout" in moves and pokemon_name.lower() not in fakeout_pokemon:
        fakeout_pokemon.append(pokemon_name.lower())
    if "tailwind" in moves and pokemon_name.lower() not in tailwind_pokemon:
        tailwind_pokemon.append(pokemon_name.lower())
    if "trickroom" in moves and pokemon_name.lower() not in trickroom_pokemon:
        trickroom_pokemon.append(pokemon_name.lower())
# ---------------------------------- VGC bot --------------------------------- #
NON_SINGLE_TARGET = ["ALL_ADJACENT_FOES", "ALL_ADJACENT", "ALL", "SELF", "ADJACENT_ALLY_OR_SELF"]
class ClamBot(Player):
    
    def choose_move(self, battle):
        
        best_score = -1
        best_order = None
        # If there is a force switch
        if any(battle.force_switch):
            left_switch = None
            right_switch = None
            if battle.force_switch[0] and battle.available_switches[0]:
                left_switch = self.create_order(battle.available_switches[0][0])
            if battle.force_switch[1] and battle.available_switches[1]:
                right_switch = self.create_order(battle.available_switches[1][0])
            if left_switch and right_switch:
                return DoubleBattleOrder(left_switch, right_switch)
            elif left_switch:
                return left_switch
            elif right_switch:
                return right_switch
    
        if battle.available_moves[0] and battle.available_moves[1]:
            for l_move in battle.available_moves[0]:
                for r_move in battle.available_moves[1]:
                    current_score = l_move.base_power + r_move.base_power
                    
                    # fakeout
                    if l_move.id == "fakeout" or r_move.id == "fakeout":
                        current_score += 500
                   
                    if current_score > best_score:
                        best_score = current_score
                        
                        # Choosing targets
                        if l_move.target.name in NON_SINGLE_TARGET:
                            l_target = 0
                        else:
                            l_target = 1
                        if r_move.target.name in NON_SINGLE_TARGET:
                            r_target = 0
                        else:
                            r_target = 2
                            
                        left_order = self.create_order(l_move, move_target=l_target)
                        right_order = self.create_order(r_move, move_target=r_target)
                        best_order = DoubleBattleOrder(left_order, right_order)
            
            return best_order
        # Only left pokemon has an avaliable move
        elif battle.available_moves[0]:
            for l_move in battle.available_moves[0]:
                current_score = l_move.base_power
                
                if l_move.id == "fakeout":
                        current_score += 500
                        
                if current_score > best_score:
                    best_score = current_score
                    
                    # Choosing target
                    if l_move.target.name in NON_SINGLE_TARGET:
                        l_target = 0
                    else:
                        l_target = 1
                        
                    left_order = self.create_order(l_move, move_target=l_target)
                    
            return left_order
        # Only right pokemon has an avaliable move
        elif battle.available_moves[1]:
            for r_move in battle.available_moves[1]:
                current_score = r_move.base_power
                
                if r_move.id == "fakeout":
                        current_score += 500
                
                if current_score > best_score:
                    best_score = current_score
                    
                    # Choosing target
                    if r_move.target.name in NON_SINGLE_TARGET:
                        r_target = 0
                    else:
                        r_target = 2
                        
                    right_order = self.create_order(r_move, move_target=r_target)
            
            return right_order
        
        else:
            print("random move")
            return self.choose_random_doubles_move(battle)
            
    
    def teampreview(self, battle):
        return self.random_teampreview(battle)
      

async def main():
    player1 = ClamBot(
        battle_format="gen9championsvgc2026regma",
        team=EX_VGC_TEAM
    )
    
    player2 = RandomPlayer(
        battle_format="gen9championsvgc2026regma",
        team=EX_VGC_TEAM
    )

    # Set n_battles=1 so you can see it complete a single match
    await player1.battle_against(player2, n_battles=3)

if __name__ == "__main__":
    asyncio.run(main())
