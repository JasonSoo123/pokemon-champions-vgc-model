import asyncio
import os
import json
import math
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
    
    def isFaster(self, my_pokemon, opp_pokemon):
        if my_pokemon is None or opp_pokemon is None or my_pokemon.fainted or opp_pokemon.fainted:
            return False
        
        # Get speed stat of my pokemon and base stats of opps
        my_speed = my_pokemon.stats.get('spe', 0)
        opp_base_speed = opp_pokemon.base_stats.get('spe', 0)
        
        # Get the speed boosts if there are any
        my_speed_boost = my_pokemon.boosts.get('spe', 0)
        opp_speed_boost = opp_pokemon.boosts.get('spe', 0)
        
        # Calculate speed
        if my_speed_boost >= 0:
            my_speed = math.floor(my_speed * ((2 + my_speed_boost)/2))
        else:
            my_speed = math.floor(my_speed * (2/(2 - my_speed_boost)))
        
        # Calculate opps speed
        if opp_speed_boost >= 0:
            opp_speed = math.floor((math.floor((2 * opp_base_speed + 31) * (1/2)) + 5) * ((2 + opp_speed_boost)/2))
        else:
            opp_speed = math.floor((math.floor((2 * opp_base_speed + 31) * (1/2)) + 5) * (2/(2 - opp_speed_boost)))

        # Check for par status
        if my_pokemon.status is not None and my_pokemon.status.name == 'PAR':
            my_speed = math.floor(my_speed * 0.5)

        if opp_pokemon.status is not None and opp_pokemon.status.name == 'PAR':
            opp_speed = math.floor(opp_speed * 0.5)
        
        return my_speed > opp_speed
    
    def choose_best_order(self, pokemon, battle, available_moves):
        best_score = -1
        best_order = None
        
        # Check if this pokemon is faster than all opponents
        pokemon_is_faster = all(self.isFaster(pokemon, opp) for opp in battle.opponent_active_pokemon)
        
        for move in available_moves:
            
            # --- Spread / Multi-Target Moves ---
            if move.target.name in NON_SINGLE_TARGET:
                total_multiplier = 0
                
                for opp in battle.opponent_active_pokemon:
                    if opp is not None and not opp.fainted:
                        total_multiplier += opp.damage_multiplier(move)
                
                current_score = move.base_power * total_multiplier
                    
                if current_score > best_score:
                    best_score = current_score
                    best_order = self.create_order(move, move_target=0)
                    
            # --- Single Target Moves ---
            else:
                # Loop through both opponents to see which one we hit harder
                for i, opp in enumerate(battle.opponent_active_pokemon):
                    if opp is not None and not opp.fainted:
                        multiplier = opp.damage_multiplier(move)
                        
                        current_score = move.base_power * multiplier
                        
                        # Scale Fake Out bonus by multiplier to prevent using it on Ghost types!
                        if move.id == "fakeout":
                            current_score += (999 * multiplier)
                            
                        if current_score > best_score:
                            best_score = current_score
                            
                            # In poke-env: Target 1 is opponent's left (index 0). Target 2 is opponent's right (index 1).
                            target = i + 1 
                            best_order = self.create_order(move, move_target=target)
        
        print(f"best order is: {best_order}")         
        return best_order
        
    
    def choose_move(self, battle):

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
            
            left_order = self.choose_best_order(battle.active_pokemon[0], battle, battle.available_moves[0])
            right_order = self.choose_best_order(battle.active_pokemon[1], battle, battle.available_moves[1])
            
            return DoubleBattleOrder(left_order, right_order)
            
        elif battle.available_moves[0]:
            return self.choose_best_order(battle.active_pokemon[0], battle, battle.available_moves[0])
            
        elif battle.available_moves[1]:
            return self.choose_best_order(battle.active_pokemon[1], battle, battle.available_moves[1])
            
        # Fallback to random selection
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
    await player1.battle_against(player2, n_battles=1)

if __name__ == "__main__":
    asyncio.run(main())
