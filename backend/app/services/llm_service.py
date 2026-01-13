"""
LLM service for AI-enhanced recommendations and explanations.

Core value: Adds natural language understanding and generation to the rule-based engine.
NOT replacing the recommendation logic, but enhancing user experience.
"""
import os
from typing import List, Dict, Optional
from openai import OpenAI

from app.models.baby import Baby
from app.models.recipe import Recipe


class LLMService:
    """
    LLM service for generating personalized explanations and insights.
    
    Why not just use ChatGPT directly?
    1. This service has access to baby's complete profile and history
    2. Uses specialized prompts optimized for infant nutrition
    3. Enforces safety constraints before/after LLM call
    4. Integrates with structured database
    5. Provides consistent, reliable responses
    """
    
    def __init__(self, api_key: Optional[str] = None):
        from app.core.config import settings
        
        # Use provided api_key, fallback to settings
        self.api_key = api_key or settings.OPENAI_API_KEY
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not configured. "
                "Set OPENAI_API_KEY in .env file or pass api_key parameter."
            )
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = settings.LLM_MODEL
    
    def generate_recipe_explanation(
        self,
        recipe: Recipe,
        baby: Baby,
        why_recommended: str
    ) -> str:
        """
        Generate personalized explanation for why a recipe is recommended.
        
        Value over raw ChatGPT:
        - Has full context (baby profile, recipe details)
        - Specialized prompt for infant nutrition
        - Consistent tone and structure
        
        Args:
            recipe: Recommended recipe
            baby: Baby profile
            why_recommended: Technical reason from recommendation engine
            
        Returns:
            Natural language explanation
        """
        prompt = f"""You are a certified infant nutrition expert. Generate a warm, informative explanation for why this recipe is recommended.

Baby Profile:
- Name: {baby.name}
- Age: {baby.get_age_months()} months ({baby.get_age_stage()} stage)
- Weight: {baby.weight_kg}kg
- Allergies: {', '.join(baby.allergies) if baby.allergies else 'None'}
- Likes: {', '.join(baby.liked_ingredients) if baby.liked_ingredients else 'exploring new foods'}

Recommended Recipe: {recipe.name}
Key nutrients:
- Protein: {recipe.protein_g}g
- Iron: {recipe.iron_mg}mg  
- Calcium: {recipe.calcium_mg}mg
- Fiber: {recipe.fiber_g}g

Technical reason: {why_recommended}

Generate a 2-3 sentence explanation that:
1. Explains nutritional benefits in parent-friendly language
2. Mentions why it's suitable for this baby's age and preferences
3. Includes one practical tip for preparation or serving

Keep it warm, encouraging, and informative."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def generate_retry_strategy(self, context: Dict) -> Dict[str, str]:
        """
        Generate retry strategy for a disliked ingredient.
        
        Args:
            context: Dictionary with ingredient, baby info, attempt history
            
        Returns:
            Strategy dict with recommendations
        """
        prompt = f"""Generate a retry strategy for introducing a food to a baby.

Ingredient: {context['ingredient']}
Baby age: {context['baby_age']} months ({context['baby_stage']} stage)
Previous attempts: {context['attempt_count']}
Foods baby likes: {', '.join(context['liked_ingredients']) if context['liked_ingredients'] else 'None yet'}
Nutritional importance: {context['nutrition_importance']}

Based on the attempt count, suggest:
1. If attempts < 3: Different preparation method
2. If attempts 3-5: Mix with favorite foods to mask taste
3. If attempts > 5: Take a break, focus on alternatives

Provide specific, actionable advice for parents.

Return JSON:
{{
  "strategy": "...",
  "rationale": "...",
  "specific_suggestion": "..."
}}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        import json
        return json.loads(response.choices[0].message.content)
    
    def answer_nutrition_question(
        self,
        question: str,
        baby: Baby,
        context_recipes: Optional[List[Recipe]] = None
    ) -> str:
        """
        Answer nutrition questions with baby-specific context.
        
        Value over raw ChatGPT:
        - Automatically includes baby's age, allergies, current diet
        - Can reference specific recipes in database
        - Grounded in baby's actual data
        
        Args:
            question: Parent's question
            baby: Baby profile
            context_recipes: Recent recipes for context
            
        Returns:
            AI-generated answer with safety disclaimer
        """
        # Build context
        context = f"""Baby Context:
- {baby.name}, {baby.get_age_months()} months old
- Current stage: {baby.get_age_stage()}
- Allergies: {', '.join(baby.allergies) if baby.allergies else 'None'}
"""
        
        if context_recipes:
            context += f"\nRecent meals:\n"
            for r in context_recipes[:5]:
                context += f"- {r.name} (Iron: {r.iron_mg}mg, Protein: {r.protein_g}g)\n"
        
        prompt = f"""You are a certified infant nutrition expert. Answer this parent's question with specific, actionable advice.

{context}

Parent's Question: {question}

Provide:
1. Direct answer to the question
2. Specific recommendations based on baby's age and profile
3. Safety considerations if any
4. One actionable next step

Keep response under 150 words. Always end with: "Note: Consult your pediatrician for personalized medical advice."
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def generate_weekly_meal_plan(
        self,
        baby: Baby,
        preferences: Dict = None
    ) -> Dict[str, List[Dict]]:
        """
        Generate structured weekly meal plan.
        
        Value over ChatGPT:
        - Returns JSON structure (easy to display/edit)
        - Ensures nutritional balance across week
        - Considers baby's profile automatically
        - Can be saved and reused
        
        Returns:
            Weekly plan with breakfast, lunch, dinner, snacks
        """
        preferences = preferences or {}
        
        prompt = f"""Generate a 7-day meal plan for a {baby.get_age_months()}-month-old baby.

Baby Profile:
- Stage: {baby.get_age_stage()}
- Allergies: {', '.join(baby.allergies) if baby.allergies else 'None'}
- Preferences: {', '.join(baby.liked_ingredients) if baby.liked_ingredients else 'None specified'}

Requirements:
- 3 meals + 2 snacks per day
- Balance protein, iron, calcium across the week
- Variety in ingredients and cuisines
- Age-appropriate textures
- Avoid allergens: {', '.join(baby.allergies) if baby.allergies else 'None'}

Return ONLY a JSON object with this structure:
{{
  "monday": {{"breakfast": "...", "lunch": "...", "dinner": "...", "snack1": "...", "snack2": "..."}},
  "tuesday": {{...}},
  ...
}}

Be specific with meal names."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.8,
            response_format={"type": "json_object"}
        )
        
        import json
        return json.loads(response.choices[0].message.content)
    
    def adapt_recipe(
        self,
        recipe: Recipe,
        adaptation_request: str,
        baby: Baby
    ) -> Dict[str, str]:
        """
        Adapt recipe based on specific needs.
        
        Examples:
        - "Make this dairy-free"
        - "Increase iron content"
        - "Simplify for a beginner cook"
        
        Value: Maintains nutritional data structure while adapting
        """
        prompt = f"""Adapt this baby food recipe based on the request.

Original Recipe: {recipe.name}
Ingredients: {[ing['name'] for ing in recipe.ingredients]}
Instructions: {recipe.instructions}

Baby: {baby.get_age_months()} months, {baby.get_age_stage()} stage
Allergies: {', '.join(baby.allergies) if baby.allergies else 'None'}

Adaptation Request: {adaptation_request}

Provide:
1. Modified ingredient list
2. Updated instructions
3. Expected nutritional changes
4. Any safety notes

Format as JSON:
{{
  "modified_ingredients": [...],
  "modified_instructions": "...",
  "nutritional_impact": "...",
  "safety_notes": "..."
}}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        import json
        return json.loads(response.choices[0].message.content)
    
    def analyze_nutrition_trend(
        self,
        baby: Baby,
        recent_meals: List[Recipe],
        time_period: str = "past week"
    ) -> str:
        """
        Analyze nutritional trends and provide insights.
        
        Value: Combines structured data analysis with natural language insights
        """
        # Calculate aggregate nutrition
        total_iron = sum(r.iron_mg or 0.0 for r in recent_meals)
        total_protein = sum(r.protein_g or 0.0 for r in recent_meals)
        total_calcium = sum(r.calcium_mg or 0.0 for r in recent_meals)
        
        prompt = f"""Analyze the nutritional trends for this baby's diet.

Baby: {baby.name}, {baby.get_age_months()} months old

Meals in {time_period} ({len(recent_meals)} meals):
{chr(10).join(f"- {r.name}: Iron {r.iron_mg}mg, Protein {r.protein_g}g, Calcium {r.calcium_mg}mg" for r in recent_meals[:10])}

Aggregate totals:
- Total iron: {total_iron:.1f}mg
- Total protein: {total_protein:.1f}g  
- Total calcium: {total_calcium:.1f}mg

Recommended weekly intake for {baby.get_age_months()}-month-old:
- Iron: 77mg (11mg/day × 7)
- Protein: 77g (11g/day × 7)
- Calcium: 1820mg (260mg/day × 7)

Provide:
1. Assessment of current nutrition (adequate/deficient/excessive)
2. Specific nutrients to focus on
3. 2-3 actionable food suggestions
4. One encouraging note for the parent

Keep under 100 words."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def chat_with_context(
        self,
        user_message: str,
        baby: Baby,
        conversation_history: List[Dict] = None
    ) -> str:
        """
        Conversational interface with full baby context.
        
        Value: ChatGPT with memory and context
        """
        conversation_history = conversation_history or []
        
        # System prompt with baby context
        system_prompt = f"""You are a certified infant nutrition assistant for {baby.name}.

Baby Profile:
- Age: {baby.get_age_months()} months ({baby.get_age_stage()} stage)
- Weight: {baby.weight_kg}kg, Height: {baby.height_cm}cm
- Allergies: {', '.join(baby.allergies) if baby.allergies else 'None'}
- Dietary restrictions: {', '.join(baby.dietary_restrictions) if baby.dietary_restrictions else 'None'}
- Favorite foods: {', '.join(baby.liked_ingredients) if baby.liked_ingredients else 'Still exploring'}

Your role:
- Provide safe, evidence-based infant nutrition advice
- Consider baby's specific profile in all responses
- Flag any safety concerns immediately
- Keep responses concise and actionable

Always end with: "Consult your pediatrician for medical concerns."
"""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content