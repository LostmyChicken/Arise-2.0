#!/usr/bin/env python3
"""
Register All Skills to Codex
Ensures all skills from skill trees and other sources are properly documented in the codex
"""

import asyncio
import logging
from structure.skills import SkillManager, Skill, SkillType, Element, EffectType
from structure.skill_tree_system import SkillTreeSystem

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def register_all_skills():
    """Register all skills from all sources to the codex"""
    try:
        # Initialize skill database
        await SkillManager.initialize()
        logging.info("✅ Skill database initialized")
        
        # Register skill tree skills
        success = await SkillTreeSystem.register_all_skills_with_manager()
        if success:
            logging.info("✅ All skill tree skills registered")
        else:
            logging.error("❌ Failed to register skill tree skills")
        
        # Add additional core skills that might not be in skill trees
        additional_skills = [
            # Basic combat skills
            Skill("punch", SkillType.BASIC, "Punch", [EffectType.DAMAGE], 50, 0, Element.FIRE),
            
            # Healing skills
            Skill("heal", SkillType.BASIC, "Heal", [EffectType.HEAL], 0, 15, Element.LIGHT),
            Skill("group_heal", SkillType.QTE, "Group Heal", [EffectType.HEAL, EffectType.BUFF], 0, 35, Element.LIGHT),
            
            # Buff skills
            Skill("taunt", SkillType.BASIC, "Taunt", [EffectType.DEBUFF], 0, 10, Element.DARK),
            Skill("shield", SkillType.QTE, "Shield", [EffectType.SHIELD, EffectType.BUFF], 0, 25, Element.LIGHT),
            
            # Elemental skills for each element
            Skill("fire_blast", SkillType.BASIC, "Fire Blast", [EffectType.DAMAGE], 75, 20, Element.FIRE),
            Skill("water_wave", SkillType.BASIC, "Water Wave", [EffectType.DAMAGE], 70, 18, Element.WATER),
            Skill("wind_slash", SkillType.BASIC, "Wind Slash", [EffectType.DAMAGE], 65, 16, Element.WIND),
            Skill("earth_spike", SkillType.BASIC, "Earth Spike", [EffectType.DAMAGE], 80, 22, Element.EARTH),
            Skill("light_beam", SkillType.QTE, "Light Beam", [EffectType.DAMAGE], 90, 30, Element.LIGHT),
            Skill("shadow_strike", SkillType.QTE, "Shadow Strike", [EffectType.DAMAGE, EffectType.DEBUFF], 85, 28, Element.DARK),
            
            # Ultimate skills
            Skill("meteor", SkillType.ULTIMATE, "Meteor", [EffectType.AREA_DAMAGE], 200, 80, Element.FIRE),
            Skill("tsunami", SkillType.ULTIMATE, "Tsunami", [EffectType.AREA_DAMAGE], 180, 75, Element.WATER),
            Skill("tornado", SkillType.ULTIMATE, "Tornado", [EffectType.AREA_DAMAGE, EffectType.DEBUFF], 190, 78, Element.WIND),
            Skill("earthquake", SkillType.ULTIMATE, "Earthquake", [EffectType.AREA_DAMAGE, EffectType.STUN], 210, 85, Element.EARTH),
            Skill("divine_judgment", SkillType.ULTIMATE, "Divine Judgment", [EffectType.DAMAGE, EffectType.HEAL], 250, 100, Element.LIGHT),
            Skill("void_consume", SkillType.ULTIMATE, "Void Consume", [EffectType.DAMAGE, EffectType.LIFE_STEAL], 220, 90, Element.DARK),
        ]
        
        # Register additional skills
        registered_additional = 0
        for skill in additional_skills:
            await SkillManager.save(skill)
            registered_additional += 1
        
        logging.info(f"✅ Registered {registered_additional} additional skills")
        
        # Verify all skills are registered
        all_skills = await SkillManager.get_all()
        logging.info(f"✅ Total skills in codex: {len(all_skills)}")
        
        # Display skill summary by type and element
        skill_summary = {}
        element_summary = {}
        
        for skill in all_skills:
            # Count by type
            skill_type = skill.skill_type.value
            if skill_type not in skill_summary:
                skill_summary[skill_type] = 0
            skill_summary[skill_type] += 1
            
            # Count by element
            element = skill.element.value
            if element not in element_summary:
                element_summary[element] = 0
            element_summary[element] += 1
        
        logging.info("📊 Skill Summary by Type:")
        for skill_type, count in sorted(skill_summary.items()):
            logging.info(f"   {skill_type}: {count} skills")
        
        logging.info("📊 Skill Summary by Element:")
        for element, count in sorted(element_summary.items()):
            logging.info(f"   {element}: {count} skills")
        
        # List all skills alphabetically
        logging.info("📚 All Skills (Alphabetical):")
        sorted_skills = sorted(all_skills, key=lambda s: s.name.lower())
        for skill in sorted_skills:
            # Check if buff-only
            is_buff_only = (skill.damage == 0 or 
                           (EffectType.BUFF in skill.effects and 
                            EffectType.DAMAGE not in skill.effects and
                            EffectType.AREA_DAMAGE not in skill.effects))
            
            damage_display = "Buff" if is_buff_only else f"{skill.damage}%"
            logging.info(f"   • {skill.name} ({skill.skill_type.value}) - {skill.element.value} - {damage_display} DMG - {skill.mp_cost} MP")
        
        logging.info("🎉 ALL SKILLS SUCCESSFULLY REGISTERED TO CODEX!")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error registering skills: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    logging.info("🚀 Starting skill registration process...")
    success = await register_all_skills()
    
    if success:
        logging.info("✅ Skill registration completed successfully!")
    else:
        logging.error("❌ Skill registration failed!")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
