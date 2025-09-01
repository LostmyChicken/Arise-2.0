from dataclasses import dataclass

@dataclass
class Stats:
    HP: int
    Attack: int
    Defense: int
    Total_Power: int
    MP: int
    Precision: int

def getStat(stat_types: list, level: int, base_stats: dict) -> Stats:
    scaling_factors = {
        "HP": 6.248,
        "Attack": 5.236,
        "Defense": 6.236,
        "Total Power": 8.458,
        "MP": 5,
        "Precision":5.458
    }

    stats = {}

    for stat_type in stat_types:
        total_scaling_factor = scaling_factors.get(stat_type, 1.0)
        
        base_stat = base_stats.get(stat_type, 0)

        if stat_type == "MP" and base_stat == 0:
            base_stat = 100

        level_scaling = 1 + (level * 0.05)  # Example: 5% increase per level (you can modify this)

        final_stat = base_stat * total_scaling_factor * level_scaling

        stats[stat_type] = round(final_stat)

    # Create and return a Stats object
    return Stats(
        HP=stats.get("HP", 0),
        Attack=stats.get("Attack", 0),
        Defense=stats.get("Defense", 0),
        Total_Power=stats.get("Total Power", 0),
        MP=stats.get("MP", 0),
        Precision=stats.get("Precision",0)
    )
