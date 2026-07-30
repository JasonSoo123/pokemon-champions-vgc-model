import asyncio
import os
import json
import math
import random
from poke_env.player import Player, RandomPlayer
from poke_env.player.battle_order import DoubleBattleOrder
from poke_env.battle.side_condition import SideCondition
from poke_env.battle.move_category import MoveCategory
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.weather import Weather
from poke_env.battle.field import Field
from poke_env.battle.status import Status

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
NON_SINGLE_TARGET = ["ALL_ADJACENT_FOES", "ALL_ADJACENT", "ALL", "SELF", "ADJACENT_ALLY_OR_SELF", "ALLY_SIDE",
                     "ALLY_TEAM", "SELF", "ADJACENT_ALLY", "SCRIPTED", "FOE_SIDE"]
class ClamBot(Player):
    
    # Helper function to determine if pokemon is faster than other pokemon
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
        print(f"my speed is: {my_speed}, opp speed is: {opp_speed}")
        return my_speed > opp_speed
    
    # Helper function to calculate damage of attacking pokemon v. defending/opp pokemon
    def calculate_damage(self, my_pokemon, opp_pokemon, move, battle):
        
        # if non damaging move return 0
        if move.base_power == 0:
            return 0
        
        # Choosing what type of stat to look for
        attacking_stat = 'atk' if move.category == MoveCategory.PHYSICAL else 'spa'
        defending_stat = 'def' if attacking_stat == 'atk' else 'spd'
        opp_base_defending_stat = opp_pokemon.base_stats.get(defending_stat, 0)
        
        # The stats of the attacking stat and defeneding stat
        pok_attacking_stat = my_pokemon.stats.get(attacking_stat, 0)
        opp_defending_stat = math.floor(math.floor((2 * opp_base_defending_stat + 31) / 2 ) + 5)
        
        # Getting the boosts
        attacking_stat_boost = my_pokemon.boosts.get(attacking_stat, 0)
        defending_stat_boost = opp_pokemon.boosts.get(defending_stat, 0)
        
        # Caclulating the attack stat if any boosts
        if attacking_stat_boost >= 0:
            pok_attacking_stat = math.floor(pok_attacking_stat * ((2 + attacking_stat_boost)/2))
        else:
            pok_attacking_stat = math.floor(pok_attacking_stat * (2/(2 - attacking_stat_boost)))
        
        # Calculating the defending stat if there are any boost
        if defending_stat_boost >= 0:
            opp_defending_stat = math.floor(opp_defending_stat * ((2 + defending_stat_boost)/2))
        else:
            opp_defending_stat = math.floor(opp_defending_stat * (2/(2 - defending_stat_boost)))
        
        # If opp pokemon is rock type and in sandstorm boost spdef by 50%
        if PokemonType.ROCK in opp_pokemon.types and battle.weather == Weather.SANDSTORM and defending_stat == "spd":
            opp_defending_stat *= 1.5
        
        # If opp pokemon is ice type and in snow boost def by 50%
        if PokemonType.ICE in opp_pokemon.types and battle.weather == Weather.SNOWSCAPE and defending_stat == "def":
            opp_defending_stat *= 1.5 
        
        # If pokemon has solar power in the sun boost spatk by 50%
        if battle.weather == Weather.SUNNYDAY and my_pokemon.ability == "solarpower" and attacking_stat == "spa":
            pok_attacking_stat *= 1.5
        
        # Calculate damage without multipliers    
        damage = math.floor(math.floor(22 * move.base_power * pok_attacking_stat / opp_defending_stat) / 50) + 2
        
        
        move_type = move.type
        
        # Modifiers for "Ate" and "Skin" abilities
        if move_type == PokemonType.NORMAL and my_pokemon.ability == "aerilate":
            
            move_type = PokemonType.FLYING
            damage *= 1.2
            
        elif move_type == PokemonType.NORMAL and my_pokemon.ability == "pixilate":
            
            move_type = PokemonType.FAIRY
            damage *= 1.2
            
        elif move_type == PokemonType.NORMAL and my_pokemon.ability == "refrigerate":
            
            move_type = PokemonType.ICE
            damage *= 1.2
        
        elif move_type == PokemonType.NORMAL and my_pokemon.ability == "galvanize":
            
            move_type = PokemonType.ELECTRIC
            damage *= 1.2
            
        elif my_pokemon.ability == "normalize":
            
            move_type = PokemonType.NORMAL
            damage *= 1.2
        
        elif my_pokemon.ability == "strongjaw" and "bite" in move.flags:
            damage *= 1.5
        
        elif my_pokemon.ability == "toughclaws" and "contact" in move.flags:
            damage *= 1.3
        
        elif my_pokemon.ability == "ironfist" and "punch" in move.flags:
            damage *= 1.2
            
        elif my_pokemon.ability == "sheerforce" and move.secondary:
            damage *= 1.3
            
        elif my_pokemon.ability == "reckless" and move.recoil is not None and move.recoil > 0:
            damage *= 1.2
            
        # Multipler if its a spread move
        if move.target.name in NON_SINGLE_TARGET:
            damage *= 0.75
        
        # Multiplier if STAB (Same Type Attack Bonus)
        if move_type in my_pokemon.types:
            if my_pokemon.ability == "adaptability":
                damage *= 2
            else:
                damage *= 1.5
        
        # If burned and physical move        
        if move.category == MoveCategory.PHYSICAL and my_pokemon.status == Status.BRN:
            damage *= 0.5
        
        # Type multiplier
        damage *= opp_pokemon.damage_multiplier(move)
        
        # Technician boost
        if my_pokemon.ability == "technician" and move.base_power <= 60:
            damage *= 1.5
        
        # If move is water type
        if move_type == PokemonType.WATER:
            
            # Weather check
            if battle.weather == Weather.RAINDANCE:
                damage *= 1.5
            elif battle.weather == Weather.SUNNYDAY:
                damage *= 0.5

            if (my_pokemon.item == "mysticwater" or my_pokemon.item == "splashplate" 
                or my_pokemon.item == "waveincense" 
                or my_pokemon.item == "seaincense"):
                
                damage *= 1.2
            
            if my_pokemon.ability == "waterbubble":
                damage *= 2
                
        # If move is fire type        
        elif move_type == PokemonType.FIRE:
            # Weather check
            if battle.weather == Weather.RAINDANCE:
                damage *= 0.5
            elif battle.weather == Weather.SUNNYDAY:
                damage *= 1.5
                
            if my_pokemon.item == "charcoal" or my_pokemon.item == "flameplate":
                damage *= 1.2
            
            if opp_pokemon.ability == "waterbubble":
                damage *= 0.5
        
        # If move is grass type
        elif move_type == PokemonType.GRASS:
            
            if (my_pokemon.item == "miracleseed" or my_pokemon.item == "meadowplate" 
                or my_pokemon.item == "roseincense"):
                damage *= 1.2
                
            if Field.GRASSY_TERRAIN in battle.fields:
                damage *= 1.5
                
        elif move_type == PokemonType.BUG:
            
            if my_pokemon.item == "silverpowder" or my_pokemon.item == "insectplate":
                damage *= 1.2
        
        elif move_type == PokemonType.DARK:
            
            if my_pokemon.item == "blackglasses" or my_pokemon.item == "dreadplate":
                damage *= 1.2
            
            if my_pokemon.ability == "darkaura":
                damage *= 1.33
                
        elif move_type == PokemonType.DRAGON:
            
            if my_pokemon.item == "dragonfang" or my_pokemon.item == "dracoplate":
                damage *= 1.2
                
            if my_pokemon.ability == "dragonsmaw":
                damage *= 1.5
        
        elif move_type == PokemonType.ELECTRIC:
            
            if my_pokemon.item == "magnet" or my_pokemon.item == "zapplate":
                damage *= 1.2
            
            if my_pokemon.ability == "transistor":
                damage *= 1.3
                
            if Field.ELECTRIC_TERRAIN in battle.fields:
                damage *= 1.5
        
        elif move_type == PokemonType.FAIRY:
            
            if my_pokemon.item == "fairyfeather" or my_pokemon.item == "pixieplate":
                damage *= 1.2
            
            if my_pokemon.ability == "fairyaura":
                damage *= 1.33
            
            if Field.MISTY_TERRAIN in battle.fields:
                damage *= 1.5
        
        elif move_type == PokemonType.FIGHTING:
            
            if my_pokemon.item == "blackbelt" or my_pokemon.item == "fistplate":
                damage *= 1.2
        
        elif move_type == PokemonType.FLYING:
            
            if my_pokemon.item == "sharpbeak" or my_pokemon.item == "skyplate":
                damage *= 1.2
        
        elif move_type == PokemonType.GHOST:
            
            if my_pokemon.item == "spelltag" or my_pokemon.item == "spookyplate":
                damage *= 1.2
        
        elif move_type == PokemonType.GROUND:
            
            if my_pokemon.item == "softsand" or my_pokemon.item == "earthplate":
                damage *= 1.2
                
            if my_pokemon.ability == "sandforce" and battle.weather == Weather.SANDSTORM:
                damage *= 1.3
        
        elif move_type == PokemonType.ICE:
            
            if my_pokemon.item == "nevermeltice" or my_pokemon.item == "icicleplate":
                damage *= 1.2
        
        elif move_type == PokemonType.NORMAL:
            
            if my_pokemon.item == "silkscarf" or my_pokemon.item == "blankplate":
                damage *= 1.2
        
        elif move_type == PokemonType.POISON:
            
            if my_pokemon.item == "poisonbarb" or my_pokemon.item == "toxicplate":
                damage *= 1.2
        
        elif move_type == PokemonType.PSYCHIC:
            
            if (my_pokemon.item == "twistedspoon" or my_pokemon.item == "mindplate" 
                or my_pokemon.item == "oddincense"):
                damage *= 1.2
            
            if Field.PSYCHIC_TERRAIN in battle.fields:
                damage *= 1.5
        
        elif move_type == PokemonType.ROCK:
            
            if (my_pokemon.item == "hardstone" or my_pokemon.item == "stoneplate" 
                or my_pokemon.item == "rockincense"):
                damage *= 1.2
            
            if my_pokemon.ability == "rockpayload":
                damage *= 1.5
            elif my_pokemon.ability == "sandforce" and battle.weather == Weather.SANDSTORM:
                damage *= 1.3
        
        elif move_type == PokemonType.STEEL:
            
            if my_pokemon.item == "metalcoat" or my_pokemon.item == "ironplate":
                damage *= 1.2
            
            if my_pokemon.ability == "steelworker" or my_pokemon.ability == "steelyspirit":
                damage *= 1.5
            elif my_pokemon.ability == "sandforce" and battle.weather == Weather.SANDSTORM:
                damage *= 1.3
                
        
        # Random roll average (0.85 - 1)
        damage = math.floor(damage * 0.925)
        
        opp_base_hp = opp_pokemon.base_stats.get("hp", 100)
        opp_hp_stat = math.floor((2 * opp_base_hp + 31) * 50 / 100 ) + 60
        
        damage_percentage = (damage / opp_hp_stat) * 100
        
        return damage_percentage
    
    # Helper function to choose the best order for a specific pokemon in the current battle
    def choose_best_order(self, pokemon, battle, available_moves):
        best_score = -1
        best_order = None
        
        for move in available_moves:
            
            # --- Spread / Multi-Target Moves / Status / (NON-SINGLE TARGET DMGING MOVES) ---
            if move.target.name in NON_SINGLE_TARGET:
                total_multiplier = 0
                
                # Tailwind conditions
                if move.id == "tailwind":
                    if SideCondition.TAILWIND in battle.side_conditions:
                        current_score = 0
                    else:
                         opp_faster = any(not self.isFaster(pokemon, opp) for opp in battle.opponent_active_pokemon if opp)
                         current_score = 98 if opp_faster else 35
                
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
                        
                        print(f"{move} does {self.calculate_damage(pokemon, opp, move, battle)} to {opp}")
                        
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
                            
                            #print(f"current best order is: {best_order} and it did {self.calculate_damage(pokemon, opp, move, battle)}")
        
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
