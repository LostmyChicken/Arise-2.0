class Rarity:
    UR = "UR"
    SSR = "SSR"
    SUPER_RARE = "Super Rare"
    RARE = "Rare"  # Keep for badge system only

    @staticmethod
    def get_all_rarities():
        return [
            Rarity.UR,
            Rarity.SSR,
            Rarity.SUPER_RARE,
        ]

    @staticmethod
    def get_all_rarities_including_legacy():
        """Include Rare for badge system only"""
        return [
            Rarity.UR,
            Rarity.SSR,
            Rarity.SUPER_RARE,
            Rarity.RARE,
        ]
