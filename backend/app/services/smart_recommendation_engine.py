"""
Smart Recommendation Engine with intelligent preference handling.
Complete fixed version with debug output.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.baby import Baby
from app.models.recipe import Recipe
from app.services.recommendation_engine import RecommendationEngine
from app.services.preference_handler import PreferenceHandler


class SmartRecommendationEngine:
    """
    Enhanced recommendation engine with LLM-powered preference handling.
    """
    
    def __init__(self, db: Session, llm_service=None):
        self.db = db
        self.rule_engine = RecommendationEngine(db)
        self.preference_handler = PreferenceHandler(db, llm_service)
        self.llm_service = llm_service
    
    def get_smart_recommendations(
        self,
        baby: Baby,
        count: int = 10,
        meal_type: str = None
    ) -> Dict[str, Any]:
        """
        Get intelligent recommendations with retry strategy.
        
        Returns dict matching SmartRecommendationResponse schema.
        """
        print(f"\n{'='*60}")
        print(f"Smart Recommendations for {baby.name} ({baby.age_months} months)")
        print(f"{'='*60}")
        
        # Get primary recommendations
        primary_recs = self._get_primary_recommendations(baby, count, meal_type)
        print(f"Primary recommendations: {len(primary_recs)}")
        
        # Get alternatives for disliked ingredients
        alternatives = self._get_alternatives_for_dislikes(baby)
        print(f"Alternatives for: {list(alternatives.keys())}")
        
        # Get retry suggestions
        retry_suggestions = self._get_retry_suggestions(baby)
        print(f"Retry suggestions: {len(retry_suggestions)}")
        
        # Generate overall explanation
        if self.llm_service:
            try:
                overall_explanation = self._generate_overall_explanation(
                    baby, primary_recs, alternatives
                )
                print(f"LLM explanation generated")
            except Exception as e:
                print(f"LLM explanation failed: {e}")
                overall_explanation = f"Personalized recommendations for {baby.name}."
        else:
            overall_explanation = f"Personalized recommendations for {baby.name} based on age and preferences."
        
        print(f"{'='*60}\n")
        
        return {
            "primary_recommendations": primary_recs,
            "alternatives": alternatives,
            "retry_suggestions": retry_suggestions,
            "overall_explanation": overall_explanation,
            "nutrition_analysis": None
        }
    
    def _get_primary_recommendations(
        self,
        baby: Baby,
        count: int,
        meal_type: str
    ) -> List[Dict]:
        """Get primary recommendations with soft penalties."""
        # Get candidates - no exclude to ensure we get results
        candidates = self.rule_engine.get_recommendations(
            baby=baby,
            count=count * 3,  # Get more candidates for better selection
            meal_type=meal_type,
            exclude_recent_days=0  # Don't exclude recent for now
        )
        
        print(f"  Rule engine returned {len(candidates)} candidates")
        
        if not candidates:
            print("  No candidates! Check database has recipes.")
            return []
        
        enhanced_recommendations = []
        
        for recipe, base_score, reason in candidates:
            # Calculate preference penalty
            penalty = self.preference_handler.calculate_preference_penalty(recipe, baby)
            adjusted_score = base_score * penalty
            
            print(f"    {recipe.name[:30]:30} base={base_score:.3f} penalty={penalty:.2f} final={adjusted_score:.3f}")
            
            # Check if retry
            is_retry = self._is_retry_recommendation(recipe, baby)
            
            # Generate explanation
            if self.llm_service and adjusted_score > 0.3:
                try:
                    explanation = self.llm_service.generate_recipe_explanation(
                        recipe, baby, reason
                    )
                except Exception as e:
                    print(f"    LLM failed for {recipe.name}: {e}")
                    explanation = reason
            else:
                explanation = reason
            
            # Serialize recipe
            recipe_dict = self._serialize_recipe(recipe)
            
            enhanced_recommendations.append({
                "recipe": recipe_dict,
                "score": adjusted_score,
                "explanation": explanation,
                "is_retry": is_retry,
                "penalty_applied": penalty < 1.0,
                "original_score": base_score,
                "nutritional_highlights": None
            })
        
        # Sort by adjusted score
        enhanced_recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        final = enhanced_recommendations[:count]
        print(f"  Selected top {len(final)} after sorting")
        
        return final
    
    def _get_alternatives_for_dislikes(self, baby: Baby) -> Dict[str, Any]:
        """Get alternatives for each disliked ingredient."""
        alternatives_dict = {}
        
        for disliked in (baby.disliked_ingredients or []):
            print(f"  Finding alternatives for '{disliked}'...")
            
            # Find nutritional alternatives
            alt_recipes = self.preference_handler.find_nutritional_alternatives(
                disliked, baby
            )
            
            # Format alternative recipes
            alternative_recipes_formatted = []
            for recipe, alt_ing, sim in alt_recipes:
                recipe_dict = self._serialize_recipe(recipe)
                alternative_recipes_formatted.append({
                    "recipe": recipe_dict,
                    "alternative_ingredient": alt_ing,
                    "similarity_score": sim,
                    "reason": f"Similar nutrition to {disliked}"
                })
            
            # Get LLM suggestions
            if self.llm_service:
                try:
                    from app.services.preference_handler import LLMAlternativeSuggester
                    suggester = LLMAlternativeSuggester(self.llm_service)
                    nutrition_group = self.preference_handler._find_nutrition_group(disliked)
                    llm_suggestions = suggester.suggest_alternatives(
                        ingredient=disliked,
                        baby=baby,
                        nutrition_group=nutrition_group,
                        reason="baby_refused"
                    )
                except Exception as e:
                    print(f"    LLM alternatives failed: {e}")
                    llm_suggestions = []
            else:
                llm_suggestions = []
            
            alternatives_dict[disliked] = {
                "ingredient": disliked,
                "nutrition_importance": self.preference_handler._get_nutrition_importance(disliked),
                "alternative_recipes": alternative_recipes_formatted,
                "llm_suggestions": llm_suggestions
            }
            
            print(f"    Found {len(alternative_recipes_formatted)} recipes, {len(llm_suggestions)} LLM suggestions")
        
        return alternatives_dict
    
    def _get_retry_suggestions(self, baby: Baby) -> List[Dict]:
        """Get retry suggestions for disliked ingredients."""
        retry_suggestions = []
        
        for disliked in (baby.disliked_ingredients or []):
            should_retry, retry_reason = self.preference_handler.should_retry_ingredient(
                disliked, baby
            )
            
            if should_retry:
                print(f"  Generating retry strategy for '{disliked}'...")
                
                # Get different preparations
                different_preps = self.preference_handler.suggest_different_preparations(
                    disliked, baby
                )
                
                # Format as list of strings
                different_preps_formatted = [
                    f"{recipe.name} ({method})"
                    for recipe, method in different_preps
                ]
                
                attempt_count = self.preference_handler._get_attempt_count(baby, disliked)
                
                # Generate retry strategy
                if self.llm_service:
                    try:
                        retry_strategy = self.preference_handler.generate_retry_recommendation(
                            disliked, baby, attempt_count
                        )
                    except Exception as e:
                        print(f"    Retry strategy generation failed: {e}")
                        retry_strategy = {"strategy": "Try different preparation", "rationale": "Progressive exposure"}
                else:
                    retry_strategy = {"strategy": "Try different preparation", "rationale": "Progressive exposure"}
                
                retry_suggestions.append({
                    "ingredient": disliked,
                    "should_retry": True,
                    "reason": retry_reason,
                    "different_preparations": different_preps_formatted,
                    "strategy": retry_strategy,
                    "attempt_count": attempt_count
                })
        
        return retry_suggestions
    
    def _serialize_recipe(self, recipe: Recipe) -> Dict:
        """Convert Recipe SQLAlchemy object to dict for Pydantic."""
        return {
            "id": recipe.id,
            "name": recipe.name,
            "description": recipe.description,
            "age_min_months": recipe.age_min_months,
            "age_max_months": recipe.age_max_months,
            "preparation_time_min": recipe.preparation_time_min,
            "difficulty_level": recipe.difficulty_level,
            "ingredients": recipe.ingredients,
            "instructions": recipe.instructions,
            "calories": recipe.calories,
            "protein_g": recipe.protein_g,
            "carbs_g": recipe.carbs_g,
            "fat_g": recipe.fat_g,
            "fiber_g": recipe.fiber_g,
            "sugar_g": recipe.sugar_g,
            "iron_mg": recipe.iron_mg,
            "calcium_mg": recipe.calcium_mg,
            "vitamin_a_mcg": recipe.vitamin_a_mcg,
            "vitamin_c_mg": recipe.vitamin_c_mg,
            "vitamin_d_mcg": recipe.vitamin_d_mcg,
            "meal_type": recipe.meal_type,
            "cuisine": recipe.cuisine,
            "tags": recipe.tags,
            "allergens": recipe.allergens,
            "serving_size_g": recipe.serving_size_g,
            "nutrition_score": recipe.get_nutrition_score()
        }
    
    def _is_retry_recommendation(self, recipe: Recipe, baby: Baby) -> bool:
        """Check if recipe contains previously disliked ingredients."""
        ingredient_names = [
            ing.get('name', '').lower() 
            for ing in (recipe.ingredients or [])
        ]
        
        for disliked in (baby.disliked_ingredients or []):
            if any(disliked.lower() in ing for ing in ingredient_names):
                return True
        
        return False
    
    def _generate_overall_explanation(
        self,
        baby: Baby,
        primary_recs: List[Dict],
        alternatives: Dict
    ) -> str:
        """Generate overall recommendation explanation using LLM."""
        if not self.llm_service:
            return f"Personalized recommendations for {baby.name}"
        
        summary_prompt = f"""Summarize this meal recommendation strategy for parents.

Baby: {baby.name}, {baby.age_months} months

Today's recommendations ({len(primary_recs)} recipes):
{chr(10).join(f"- {rec['recipe']['name']}" for rec in primary_recs[:5])}

Foods being retried: {len([r for r in primary_recs if r['is_retry']])}
Alternative ingredients suggested: {len(alternatives)}

Write a brief, warm message (2-3 sentences) explaining the strategy.
Keep it encouraging and parent-friendly."""

        try:
            response = self.llm_service.client.chat.completions.create(
                model=self.llm_service.model,
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM explanation failed: {e}")
            return f"Personalized recommendations for {baby.name} based on nutritional needs and preferences."