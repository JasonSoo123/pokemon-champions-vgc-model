import asyncio
from poke_env.player import Player, RandomPlayer

EX_VGC_TEAM = '''
Charizard @ Charizardite Y  
Ability: Blaze  
Level: 50  
EVs: 2 Atk / 32 SpA / 32 Spe  
Hasty Nature  
- Acrobatics  
- Air Slash  
- Ancient Power  
- Body Slam  

Blastoise @ Blastoisinite  
Ability: Torrent  
Level: 50  
EVs: 32 HP / 32 Atk / 2 SpA  
Brave Nature  
- Aqua Jet  
- Aqua Tail  
- Aura Sphere  
- Avalanche  

Palafin @ Choice Scarf  
Ability: Zero to Hero  
Level: 50  
EVs: 2 Atk / 32 SpA / 32 Spe  
Naive Nature  
- Aqua Tail  
- Aura Sphere  
- Blizzard  
- Boomburst  

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

'''

class ClamBot(Player):
    def choose_move(self, battle):
        return self.choose_random_doubles_move(battle)

    def teampreview(self, battle):
        return self.random_teampreview(battle)

async def main():
    player1 = ClamBot(
        battle_format="gen9championsvgc2026regma",
        team=EX_VGC_TEAM
    )
    
    player2 = ClamBot(
        battle_format="gen9championsvgc2026regma",
        team=EX_VGC_TEAM
    )

    # Set n_battles=1 so you can see it complete a single match
    await player1.battle_against(player2, n_battles=2)

if __name__ == "__main__":
    asyncio.run(main())
