"""
Intelligent preference handling service.

Core insight: Disliked ingredients should not be completely filtered.
Instead:
1. Lower their recommendation score (soft penalty)
2. Suggest nutritionally similar alternatives (LLM)
3. Recommend different preparation methods
4. Track retry attempts and adjust strategy

This is where LLM adds real value over simple filtering.
"""
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.models.baby import Baby
from app.models.recipe import Recipe


class PreferenceHandler:
    """
    Handles intelligent preference-based filtering and suggestions.
    
    Philosophy: Never completely exclude foods, always offer alternatives.
    """
    
    # Nutritional similarity mapping (used for LLM prompts)
    NUTRITION_GROUPS = {
        "vitamin_a_sources": ["carrot", "sweet potato", "pumpkin", "spinach", "mango"],
        "iron_sources": ["red lentils", "beef", "chicken", "spinach", "fortified cereal"],
        "calcium_sources": ["yogurt", "cheese", "tofu", "broccoli", "fortified milk"],
        "protein_sources": ["chicken", "beef", "lentils", "beans", "tofu", "eggs"],
        "vitamin_c_sources": ["orange", "strawberry", "kiwi", "bell pepper", "broccoli"]
    }
    
    def __init__(self, db: Session, llm_service=None):
        self.db = db
        self.llm_service = llm_service
    
    def handle_disliked_ingredient(
        self,
        ingredient: str,
        baby: Baby,
        reason: str = "baby_refused"
    ) -> Dict[str, any]:
        """
        Handle when baby dislikes an ingredient.
        
        Instead of filtering it out:
        1. Find nutritionally similar alternatives
        2. Suggest different preparations
        3. Plan retry strategy
        
        Args:
            ingredient: Disliked ingredient name
            baby: Baby profile
            reason: Why disliked (texture/taste/refused/etc)
            
        Returns:
            Strategy dict with alternatives and retry plan
        """
        # Find nutrition group
        nutrition_group = self._find_nutrition_group(ingredient)
        
        # Generate alternatives using LLM (if available)
        if self.llm_service:
            alternatives = self.llm_service.suggest_alternatives(
                ingredient=ingredient,
                baby=baby,
                nutrition_group=nutrition_group,
                reason=reason
            )
        else:
            # Fallback: rule-based alternatives
            alternatives = self._get_fallback_alternatives(ingredient, nutrition_group)
        
        # Plan retry strategy
        retry_plan = self._create_retry_plan(ingredient, baby, reason)
        
        return {
            "ingredient": ingredient,
            "alternatives": alternatives,
            "retry_plan": retry_plan,
            "nutrition_group": nutrition_group
        }
    
    def calculate_preference_penalty(
        self,
        recipe: Recipe,
        baby: Baby
    ) -> float:
        """
        Calculate preference penalty instead of binary filter.
        
        Strategy:
        - First rejection: 0.7x penalty (still recommend, but lower)
        - Second rejection: 0.4x penalty
        - Third rejection: 0.1x penalty (nearly filtered)
        - BUT: Never completely filter (always give chance to retry)
        
        Args:
            recipe: Recipe to score
            baby: Baby profile
            
        Returns:
            Penalty multiplier (0.1 - 1.0)
        """
        penalty = 1.0  # Start with no penalty
        
        ingredient_names = [
            ing.get('name', '').lower() 
            for ing in (recipe.ingredients or [])
        ]
        
        # Check each disliked ingredient
        for disliked in (baby.disliked_ingredients or []):
            if any(disliked.lower() in ing for ing in ingredient_names):
                # Check attempt history
                attempts = self._get_attempt_count(baby, disliked)
                
                if attempts == 0:
                    penalty *= 0.7  # First time disliked
                elif attempts == 1:
                    penalty *= 0.4  # Second rejection
                else:
                    penalty *= 0.1  # Multiple rejections
        
        return max(penalty, 0.1)  # Never go below 0.1
    
    def should_retry_ingredient(
        self,
        ingredient: str,
        baby: Baby
    ) -> Tuple[bool, str]:
        """
        Decide if it's time to retry a disliked ingredient.
        
        Retry conditions:
        1. At least 2 weeks since last attempt
        2. Baby is older (taste changes with age)
        3. Different preparation method
        
        Returns:
            (should_retry, reason)
        """
        attempt_history = self._get_attempt_history(baby, ingredient)
        
        if not attempt_history:
            return True, "Never tried before"
        
        last_attempt_date = attempt_history.get('last_try')
        if last_attempt_date:
            days_since = (date.today() - last_attempt_date).days
            
            # Wait at least 14 days between retries
            if days_since < 14:
                return False, f"Too soon (only {days_since} days since last try)"
            
            # More lenient retry for older babies
            baby_age = baby.age_months
            if baby_age > 10 and days_since >= 30:
                return True, "Baby is older, tastes may have changed"
        
        # Check if we've tried different preparations
        attempts = attempt_history.get('attempts', 0)
        if attempts < 3:
            return True, f"Only tried {attempts} times, worth another attempt"
        
        return False, "Multiple rejections, focus on alternatives"
    
    def find_nutritional_alternatives(
        self,
        disliked_ingredient: str,
        baby: Baby
    ) -> List[Tuple[Recipe, str, float]]:
        """
        Find recipes with similar nutrition but different ingredients.
        
        Example:
        Disliked: "carrot" (Vitamin A source)
        Alternatives: Sweet potato, pumpkin recipes (also Vitamin A)
        
        Returns:
            List of (recipe, alternative_ingredient, nutrition_similarity_score)
        """
        # Find nutrition group
        nutrition_group = self._find_nutrition_group(disliked_ingredient)
        
        if not nutrition_group:
            return []
        
        # Get alternative ingredients from same nutrition group
        alternatives = [
            ing for ing in self.NUTRITION_GROUPS.get(nutrition_group, [])
            if ing.lower() != disliked_ingredient.lower()
        ]
        
        # Find recipes containing alternatives
        alternative_recipes = []
        
        for alt_ingredient in alternatives:
            # Query recipes containing this alternative
            recipes = self.db.query(Recipe).filter(
                Recipe.age_min_months <= baby.age_months
            ).all()
            
            for recipe in recipes:
                ingredient_names = [
                    ing.get('name', '').lower() 
                    for ing in (recipe.ingredients or [])
                ]
                
                # Check if contains alternative ingredient
                if any(alt_ingredient in ing for ing in ingredient_names):
                    # Calculate nutrition similarity
                    similarity = self._calculate_nutrition_similarity(
                        disliked_ingredient, alt_ingredient
                    )
                    
                    alternative_recipes.append((recipe, alt_ingredient, similarity))
        
        # Sort by similarity
        alternative_recipes.sort(key=lambda x: x[2], reverse=True)
        
        return alternative_recipes[:5]  # Top 5 alternatives
    
    def suggest_different_preparations(
        self,
        ingredient: str,
        baby: Baby
    ) -> List[Tuple[Recipe, str]]:
        """
        Find different ways to prepare the same ingredient.
        
        Example:
        Ingredient: "carrot"
        Rejected: "Carrot Puree" (steamed, mashed)
        Suggestions:
        - "Carrot Fingers" (roasted, finger food)
        - "Carrot Pancakes" (mixed with banana, hidden)
        - "Carrot Juice" (fresh, different texture)
        
        Returns:
            List of (recipe, preparation_method)
        """
        # Query all recipes with this ingredient
        recipes = self.db.query(Recipe).filter(
            Recipe.age_min_months <= baby.age_months
        ).all()
        
        matching_recipes = []
        
        for recipe in recipes:
            ingredient_names = [
                ing.get('name', '').lower() 
                for ing in (recipe.ingredients or [])
            ]
            
            if any(ingredient.lower() in ing for ing in ingredient_names):
                # Infer preparation method from recipe
                prep_method = self._infer_preparation_method(recipe)
                matching_recipes.append((recipe, prep_method))
        
        return matching_recipes
    
    def generate_retry_recommendation(
        self,
        disliked_ingredient: str,
        baby: Baby,
        attempt_count: int
    ) -> Dict[str, any]:
        """
        Generate intelligent retry recommendation using LLM.
        
        Strategy based on attempt count:
        - Attempt 1-2: Try different preparation
        - Attempt 3-4: Mix with favorite foods
        - Attempt 5+: Focus on alternatives, occasional retry
        
        This is where LLM shines: contextual, personalized advice.
        """
        if self.llm_service is None:
            return self._fallback_retry_strategy(disliked_ingredient, attempt_count)
        
        # Build context for LLM
        context = {
            "ingredient": disliked_ingredient,
            "baby_age": baby.age_months,
            "baby_stage": baby.age_stage,
            "attempt_count": attempt_count,
            "liked_ingredients": baby.liked_ingredients or [],
            "nutrition_importance": self._get_nutrition_importance(disliked_ingredient)
        }
        
        # LLM generates personalized strategy
        strategy = self.llm_service.generate_retry_strategy(context)
        
        return strategy
    
    def _find_nutrition_group(self, ingredient: str) -> Optional[str]:
        """Find which nutrition group an ingredient belongs to."""
        ingredient_lower = ingredient.lower()
        
        for group, ingredients in self.NUTRITION_GROUPS.items():
            if any(ingredient_lower in ing.lower() or ing.lower() in ingredient_lower 
                   for ing in ingredients):
                return group
        
        return None
    
    def _calculate_nutrition_similarity(
        self,
        ingredient1: str,
        ingredient2: str
    ) -> float:
        """
        Calculate nutritional similarity between two ingredients.
        
        Simplified version: checks if in same nutrition group.
        Could be enhanced with actual nutrient composition comparison.
        """
        group1 = self._find_nutrition_group(ingredient1)
        group2 = self._find_nutrition_group(ingredient2)
        
        if group1 and group1 == group2:
            return 0.9  # Same nutrition group
        
        # Could enhance: compare actual nutrient profiles
        # For now, return moderate similarity
        return 0.5
    
    def _get_attempt_count(self, baby: Baby, ingredient: str) -> int:
        """Get how many times baby has tried and rejected this ingredient."""
        # This would query baby's tried_ingredients JSON field
        tried = baby.tried_ingredients or {}
        return tried.get(ingredient, {}).get('attempts', 0)
    
    def _get_attempt_history(self, baby: Baby, ingredient: str) -> Dict:
        """Get full attempt history for an ingredient."""
        tried = baby.tried_ingredients or {}
        return tried.get(ingredient, {})
    
    def _infer_preparation_method(self, recipe: Recipe) -> str:
        """Infer preparation method from recipe details."""
        name_lower = recipe.name.lower()
        instructions_lower = (recipe.instructions or "").lower()
        
        if "puree" in name_lower or "mash" in instructions_lower:
            return "pureed"
        elif "finger" in name_lower or "stick" in name_lower:
            return "finger_food"
        elif "pancake" in name_lower or "muffin" in name_lower:
            return "baked_mixed"
        elif "steam" in instructions_lower:
            return "steamed"
        elif "roast" in instructions_lower or "bake" in instructions_lower:
            return "roasted"
        else:
            return "other"
    
    def _get_nutrition_importance(self, ingredient: str) -> str:
        """Get why this ingredient is nutritionally important."""
        nutrition_importance = {
            "spinach": "rich in iron and folate, crucial for blood health",
            "carrot": "high in vitamin A, essential for vision and immune system",
            "broccoli": "contains vitamin C, K, and fiber",
            "lentils": "excellent plant-based protein and iron source",
            "yogurt": "provides calcium and probiotics for gut health"
        }
        
        for key, importance in nutrition_importance.items():
            if key in ingredient.lower():
                return importance
        
        return "important for balanced nutrition"
    
    def _create_retry_plan(
        self,
        ingredient: str,
        baby: Baby,
        reason: str
    ) -> Dict[str, any]:
        """Create structured retry plan."""
        return {
            "next_retry_date": date.today() + timedelta(days=14),
            "suggested_preparation": "different from previous attempt",
            "mixing_strategy": f"Try mixing with {baby.liked_ingredients[0] if baby.liked_ingredients else 'favorite food'}",
            "max_attempts": 5,
            "current_attempts": self._get_attempt_count(baby, ingredient)
        }
    
    def _fallback_retry_strategy(
        self,
        ingredient: str,
        attempt_count: int
    ) -> Dict[str, str]:
        """Fallback strategy when LLM unavailable."""
        strategies = {
            1: f"Try {ingredient} in a different form (e.g., roasted instead of pureed)",
            2: f"Mix {ingredient} with a favorite food to mask the taste",
            3: f"Offer {ingredient} when baby is very hungry",
            4: f"Focus on nutritional alternatives while occasionally offering {ingredient}",
            5: f"Consider {ingredient} again after 1 month as tastes change"
        }
        
        return {
            "strategy": strategies.get(min(attempt_count, 5), strategies[5]),
            "rationale": "Progressive exposure approach"
        }
    
    def _get_fallback_alternatives(
        self,
        ingredient: str,
        nutrition_group: Optional[str]
    ) -> List[Dict[str, str]]:
        """Fallback alternatives when LLM unavailable."""
        if not nutrition_group:
            return []
        
        alternatives_list = PreferenceHandler.NUTRITION_GROUPS.get(nutrition_group, [])
        
        return [
            {
                "ingredient": alt,
                "reason": f"Similar nutrition to {ingredient}",
                "preparation_tip": "Steam or puree for easy digestion"
            }
            for alt in alternatives_list[:3]
            if alt.lower() != ingredient.lower()
        ]


class LLMAlternativeSuggester:
    """
    Uses LLM to suggest intelligent alternatives for disliked ingredients.
    
    This is the killer feature that ChatGPT alone can't provide.
    """
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
    
    def suggest_alternatives(
        self,
        ingredient: str,
        baby: Baby,
        nutrition_group: Optional[str] = None,
        reason: str = "baby_refused"
    ) -> List[Dict[str, str]]:
        """
        Use LLM to suggest alternatives with explanations.
        
        Value proposition: 
        - Contextual suggestions based on baby's profile
        - Explains WHY the alternative is good
        - Considers preparation methods
        """
        prompt = f"""You are an infant nutrition expert. A baby rejected {ingredient}.

Baby Profile:
- Age: {baby.age_months} months ({baby.age_stage} stage)
- Already likes: {', '.join(baby.liked_ingredients) if baby.liked_ingredients else 'still exploring'}
- Rejection reason: {reason}

Nutritional role of {ingredient}: {self._get_nutritional_role(ingredient, nutrition_group)}

Suggest 3 alternatives that:
1. Provide similar nutrition
2. Have different taste/texture
3. Are age-appropriate
4. Consider what baby already likes

For each alternative, explain:
- Why nutritionally equivalent
- Why baby might prefer it
- How to prepare it

Format as JSON:
{{
  "alternatives": [
    {{
      "ingredient": "...",
      "reason": "...",
      "preparation_tip": "..."
    }}
  ],
  "general_advice": "..."
}}
"""

        # Call LLM
        response = self.llm_service.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=400
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        return result.get('alternatives', [])
    
    def suggest_preparation_variations(
        self,
        ingredient: str,
        baby: Baby,
        rejected_method: str
    ) -> List[Dict[str, str]]:
        """
        Suggest different ways to prepare the same ingredient.
        
        Example:
        Input: "carrot", rejected_method="pureed"
        Output: 
        - Roasted carrot sticks (finger food, sweet and caramelized)
        - Carrot hidden in banana muffins
        - Fresh carrot juice mixed with apple
        """
        prompt = f"""A {baby.age_months}-month-old baby rejected {ingredient} prepared as {rejected_method}.

Suggest 3 different preparation methods for {ingredient} that:
1. Are suitable for {baby.age_stage} stage
2. Offer different taste/texture than {rejected_method}
3. Are practical for busy parents
4. Preserve nutritional value

Baby's favorites: {', '.join(baby.liked_ingredients) if baby.liked_ingredients else 'None yet'}

Format as JSON:
{{
  "preparations": [
    {{
      "method": "...",
      "recipe_idea": "...",
      "why_different": "...",
      "parent_tip": "..."
    }}
  ]
}}
"""

        response = self.llm_service.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=400
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        return result.get('preparations', [])
    
    def _get_nutritional_role(
        self,
        ingredient: str,
        nutrition_group: Optional[str]
    ) -> str:
        """Get explanation of ingredient's nutritional importance."""
        roles = {
            "vitamin_a_sources": "Essential for vision, immune function, and skin health",
            "iron_sources": "Critical for blood formation and cognitive development",
            "calcium_sources": "Vital for bone development and muscle function",
            "protein_sources": "Building blocks for growth and development",
            "vitamin_c_sources": "Supports immune system and iron absorption"
        }
        
        return roles.get(nutrition_group, "Important for balanced nutrition")