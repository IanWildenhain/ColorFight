from colorfight import Colorfight
import time
import random
from colorfight.constants import BLD_GOLD_MINE, BLD_ENERGY_WELL, BLD_FORTRESS, BUILDING_COST

uid = 0;

def sortEnergy(cell):
    return cell.energy

def sortGold(cell):
    return cell.gold

def sort(cell):
    e = cell.energy
    g = cell.gold
    c = cell.attack_cost
    b = 0
    if (cell.owner != uid and cell.owner != 0):
        b += 0.5
        if not cell.building.is_empty:
            b += 0.5
    return (10 * (3*e + g) / c) + b

def sort2(cell):
    e = cell.energy
    g = cell.gold
    c = cell.attack_cost
    b = 0
    if (cell.owner != uid):
        b += 1
        if not cell.building.is_empty:
            b += 1.5
    return (10 * (3*e + g) / c) + b;

def sortMax(cell):
    return max (cell.natural_energy, cell.natural_gold)

def earlyearlygame(game):
    return game.turn <25

def earlygame (game):
    return game.turn <110

def lategame (game):
    return game.turn >400

def midgame (game):
    return not earlygame(game) and not lategame(game)

def play_game(
        game, \
        room,      \
        username , \
        password) :
    # Connect to the server. This will connect to the public room. If you want to
    # join other rooms, you need to change the argument
    game.connect(room = room)
    
    # game.register should return True if succeed.
    # As no duplicate usernames are allowed, a random integer string is appended
    # to the example username. You don't need to do this, change the username
    # to your ID.
    # You need to set a password. For the example AI, the current time is used
    # as the password. You should change it to something that will not change 
    # between runs so you can continue the game if disconnected.
    if game.register(username = username, \
            password = password):
        # This is the game loop
        while True:
            # The command list we will send to the server
            cmd_list = []
            # The list of cells that we want to attack
            my_attack_list = []
            # update_turn() is required to get the latest information from the
            # server. This will halt the program until it receives the updated
            # information. 
            # After update_turn(), game object will be updated.   
            # update_turn() returns a Boolean value indicating if it's still 
            # the same game. If it's not, break out
            if not game.update_turn():
                break
    
            # Check if you exist in the game. If not, wait for the next round.
            # You may not appear immediately after you join. But you should be 
            # in the game after one round.
            if game.me == None:
                continue
    
            me = game.me
            uid = me.uid
            adjacent_cells = set()
            list_mycells = list()
            set_adj_to_enemy = set()

            num_buildings = 0

            gold_rush = False

            if (me.energy >= 150000 or game.turn >= 400):
                gold_rush = True
            

            # add uncontrolled cells which are in reach to a set - these are the cells that can be attacked
            for cell in game.me.cells.values():
                if cell.owner == me.uid:
                    if (cell.building.is_home):
                        home = cell
                    list_mycells.append(cell)
                    if not cell.building.is_empty:
                        num_buildings += 1
                    for pos in cell.position.get_surrounding_cardinals():
                        c = game.game_map[pos]
                        if c.owner != me.uid:
                            adjacent_cells.add(c)
                        if c.owner != me.uid and c.owner != 0:
                            set_adj_to_enemy.add(cell)

            
            list_adj = list(adjacent_cells)
            list_adj.sort(key = sort, reverse = True)


            #prioritize upgrading home since it can maximize resources with upgrades
            if(home.building.can_upgrade and me.gold >= home.building.upgrade_gold and me.energy >= home.building.upgrade_energy and num_buildings > 10):
                cmd_list.append(game.upgrade(home.position))
                me.gold -= home.building.upgrade_gold
                me.energy -= home.building.upgrade_energy


            #lategame stage (want gold)
            if (gold_rush):
                list_mycells.sort(key = sortGold, reverse = True)

                for cell in list_mycells:
                    if (not cell.building.is_empty and cell.building.name == "gold_mine" and cell.building.can_upgrade and me.gold >= cell.building.upgrade_gold):
                        cmd_list.append(game.upgrade(cell.position))
                        me.gold -= cell.building.upgrade_gold
                        list_mycells.remove(cell)
                    if( cell.building.is_empty and me.gold >= 200):
                        cmd_list.append(game.build(cell.position, BLD_GOLD_MINE))
                        list_mycells.remove(cell)
                        me.gold -= 200
 

            
            #to break imbalance between energy and source
            if( not gold_rush and (me.energy_source > me.gold_source * 1.7 and me.energy_source > me.gold_source + 1700)):
                list_mycells.sort(key = sortGold, reverse = True)

                num_gold_built = 0
                for cell in list_mycells:
                    if(not cell.building.is_empty and cell.building.name == "gold_mine" and cell.building.can_upgrade and me.gold >= cell.building.upgrade_gold):
                        cmd_list.append(game.upgrade(cell.position))
                        me.gold -= cell.building.upgrade_gold
                        list_mycells.remove(cell)
                    if( cell.building.is_empty and cell.gold > 7 and cell.gold - cell.energy >= 4 and num_gold_built < 3 and me.gold >= 200):
                        cmd_list.append(game.build(cell.position, BLD_GOLD_MINE))
                        list_mycells.remove(cell)
                        me.gold -= 200
                        num_gold_built += 1



            list_mycells.sort(key = sortEnergy, reverse = True)

            for cell in list_mycells:
                if(not gold_rush and not cell.building.is_empty and me.energy < 150000 and cell.building.name == "energy_well" and cell.building.can_upgrade and me.gold >= cell.building.upgrade_gold):
                    cmd_list.append(game.upgrade(cell.position))
                    me.gold -= cell.building.upgrade_gold
                    list_mycells.remove(cell)
                if(cell.building.is_empty and cell.energy >= 5):
                    if(not gold_rush and me.gold >= 200):
                        cmd_list.append(game.build(cell.position, BLD_ENERGY_WELL))
                        me.gold -= 200
                        list_mycells.remove(cell)




            if (len(list_adj) > 0):
                if( list_adj[0].attack_cost + 1 < me.energy):
                        cmd_list.append(game.attack(list_adj[0].position, list_adj[0].attack_cost + 1))
                        me.energy -= list_adj[0].attack_cost + 1
                        my_attack_list.append(list_adj[0].position)

                for i in range(1, len(list_adj)):
                    cell = list_adj[i]

                    if(cell.attack_cost + 1 < me.energy and cell.energy >= 5):
                        cmd_list.append(game.attack(cell.position, cell.attack_cost + 1))
                        me.energy -= cell.attack_cost + 1
                        my_attack_list.append(cell.position)


            # # game.me.cells is a dict, where the keys are Position and the values
            # # are MapCell. Get all my cells.
            # for cell in game.me.cells.values():
            #     # Check the surrounding position
            #     for pos in cell.position.get_surrounding_cardinals():
            #         # Get the MapCell object of that position
            #         c = game.game_map[pos]
            #         # Attack if the cost is less than what I have, and the owner
            #         # is not mine, and I have not attacked it in this round already
            #         # We also try to keep our cell number under 100 to avoid tax
            #         if c.attack_cost < me.energy and c.owner != game.uid \
            #                 and c.position not in my_attack_list \
            #                 and len(me.cells) < 95:
            #             # Add the attack command in the command list
            #             # Subtract the attack cost manually so I can keep track
            #             # of the energy I have.
            #             # Add the position to the attack list so I won't attack
            #             # the same cell
            #             cmd_list.append(game.attack(pos, c.attack_cost))
            #             print("We are attacking ({}, {}) with {} energy".format(pos.x, pos.y, c.attack_cost))
            #             game.me.energy -= c.attack_cost
            #             my_attack_list.append(c.position)
    
            #     # If we can upgrade the building, upgrade it.
            #     # Notice can_update only checks for upper bound. You need to check
            #     # tech_level by yourself. 
            #     if cell.building.can_upgrade and \
            #             (cell.building.is_home or cell.building.level < me.tech_level) and \
            #             cell.building.upgrade_gold < me.gold and \
            #             cell.building.upgrade_energy < me.energy:
            #         cmd_list.append(game.upgrade(cell.position))
            #         print("We upgraded ({}, {})".format(cell.position.x, cell.position.y))
            #         me.gold   -= cell.building.upgrade_gold
            #         me.energy -= cell.building.upgrade_energy
                    
            #     # Build a random building if we have enough gold
            #     if cell.owner == me.uid and cell.building.is_empty and me.gold >= BUILDING_COST[0]:
            #         building = random.choice([BLD_FORTRESS, BLD_GOLD_MINE, BLD_ENERGY_WELL])
            #         cmd_list.append(game.build(cell.position, building))
            #         print("We build {} on ({}, {})".format(building, cell.position.x, cell.position.y))
            #         me.gold -= 100
    
            
            # Send the command list to the server
            result = game.send_cmd(cmd_list)
            print(result)

    # Do this to release all the allocated resources. 
    game.disconnect()

if __name__ == '__main__':
    # Create a Colorfight Instance. This will be the object that you interact
    # with.
    game = Colorfight()

    # ================== Find a random non-full rank room ==================
    #room_list = game.get_gameroom_list()
    #rank_room = [room for room in room_list if room["rank"] and room["player_number"] < room["max_player"]]
    #room = random.choice(rank_room)["name"]
    # ======================================================================
    room = 'public' # Delete this line if you have a room from above

    username = 'hihihii'
    password = 'pass'

    # ==========================  Play game once ===========================
    play_game(
        game     = game, \
        room     = room, \
        username = username, \
        password = password
    )
    # ======================================================================

    # ========================= Run my bot forever =========================
    # while True:
    #     try:
    #         play_game(
    #             game     = game, \
    #             room     = room, \
    #             username = username, \
    #             password = password
    #         )
    #     except Exception as e:
    #         print(e)
    #         time.sleep(2)