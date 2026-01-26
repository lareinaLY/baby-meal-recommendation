/**
 * Smart Recommendations Component
 * Displays AI-enhanced recipe recommendations with alternatives and feedback
 */
import { useState } from 'react';
import { 
  ChefHat, 
  Clock, 
  TrendingUp, 
  AlertTriangle, 
  ChevronDown, 
  ChevronUp,
  Sparkles,
  RefreshCw
} from 'lucide-react';
import FeedbackButtons from './FeedbackButtons';

export default function SmartRecommendations({ recommendations, baby, onFeedbackSubmitted }) {
  const [expandedAlternatives, setExpandedAlternatives] = useState({});
  const [expandedRecipe, setExpandedRecipe] = useState(null);

  if (!recommendations) {
    return (
      <div className="text-center py-12 text-gray-500">
        <ChefHat size={48} className="mx-auto mb-4 text-gray-400" />
        <p>Get recommendations to see AI-powered suggestions</p>
      </div>
    );
  }

  const { primary_recommendations, alternatives, retry_suggestions, overall_explanation } = recommendations;

  const toggleAlternative = (ingredient) => {
    setExpandedAlternatives(prev => ({
      ...prev,
      [ingredient]: !prev[ingredient]
    }));
  };

  const toggleRecipe = (recipeId) => {
    setExpandedRecipe(expandedRecipe === recipeId ? null : recipeId);
  };

  console.log('Rendering SmartRecommendations:', {
    primary_count: primary_recommendations?.length || 0,
    alternatives_keys: Object.keys(alternatives || {}),
    retry_count: retry_suggestions?.length || 0
  });

  return (
    <div className="space-y-6">
      {/* Overall Explanation */}
      {overall_explanation && (
        <div className="bg-gradient-to-r from-primary-50 to-blue-50 border border-primary-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Sparkles className="text-primary-600 flex-shrink-0 mt-1" size={20} />
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">AI Insights</h3>
              <p className="text-gray-700 text-sm leading-relaxed">{overall_explanation}</p>
            </div>
          </div>
        </div>
      )}

      {/* Primary Recommendations */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <ChefHat size={20} className="text-primary-600" />
          Recommended Recipes for {baby?.name}
        </h3>

        {!primary_recommendations || primary_recommendations.length === 0 ? (
          <div className="text-center py-8 bg-gray-50 rounded-lg">
            <p className="text-gray-500">No recommendations available.</p>
            <p className="text-sm text-gray-400 mt-2">Check console for errors or try refreshing.</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {primary_recommendations.map((rec, index) => (
              <div
                key={rec.recipe.id}
                className={`recipe-card bg-white rounded-lg shadow-sm border-2 transition-all ${
                  rec.is_retry 
                    ? 'border-yellow-300 bg-yellow-50' 
                    : rec.penalty_applied
                    ? 'border-orange-200'
                    : 'border-gray-200'
                }`}
              >
                <div className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold text-gray-900 text-lg">
                          {index + 1}. {rec.recipe.name}
                        </h4>
                        {rec.is_retry && (
                          <span className="px-2 py-1 bg-yellow-200 text-yellow-800 text-xs font-medium rounded-full flex items-center gap-1">
                            <RefreshCw size={12} />
                            Retry
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600">{rec.recipe.description}</p>
                    </div>
                    
                    {/* Score Badge */}
                    <div className="flex-shrink-0 ml-4">
                      <div className="text-center">
                        <div className={`text-2xl font-bold ${
                          rec.score > 0.7 ? 'text-green-600' :
                          rec.score > 0.5 ? 'text-yellow-600' : 'text-gray-600'
                        }`}>
                          {Math.round(rec.score * 100)}
                        </div>
                        <div className="text-xs text-gray-500">Match</div>
                      </div>
                    </div>
                  </div>

                  {/* AI Explanation */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                    <div className="flex items-start gap-2">
                      <Sparkles size={16} className="text-blue-600 flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {rec.explanation}
                      </p>
                    </div>
                  </div>

                  {/* Quick Info */}
                  <div className="flex flex-wrap gap-4 text-sm text-gray-600 mb-3">
                    <div className="flex items-center gap-1">
                      <Clock size={16} />
                      <span>{rec.recipe.preparation_time_min || '15'} min</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <TrendingUp size={16} />
                      <span>Nutrition: {Math.round(rec.recipe.nutrition_score)}/100</span>
                    </div>
                    <div>
                      <span className="text-xs px-2 py-1 bg-gray-100 rounded-full">
                        {rec.recipe.difficulty_level || 'easy'}
                      </span>
                    </div>
                  </div>

                  {/* Feedback Buttons */}
                  <div className="mb-3">
                    <FeedbackButtons 
                      baby={baby} 
                      recipe={rec.recipe} 
                      onFeedbackSubmitted={onFeedbackSubmitted}
                    />
                  </div>

                  {/* Expandable Details Button */}
                  <button
                    onClick={() => toggleRecipe(rec.recipe.id)}
                    className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1 font-medium"
                  >
                    {expandedRecipe === rec.recipe.id ? (
                      <>
                        <ChevronUp size={16} />
                        Hide details
                      </>
                    ) : (
                      <>
                        <ChevronDown size={16} />
                        View ingredients & instructions
                      </>
                    )}
                  </button>

                  {/* Expanded Details */}
                  {expandedRecipe === rec.recipe.id && (
                    <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
                      {/* Ingredients */}
                      <div>
                        <h5 className="font-medium text-gray-900 mb-2">Ingredients:</h5>
                        <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                          {rec.recipe.ingredients.map((ing, i) => (
                            <li key={i}>
                              {ing.quantity} {ing.unit} {ing.name}
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Instructions */}
                      {rec.recipe.instructions && (
                        <div>
                          <h5 className="font-medium text-gray-900 mb-2">Instructions:</h5>
                          <p className="text-sm text-gray-700 whitespace-pre-line">
                            {rec.recipe.instructions}
                          </p>
                        </div>
                      )}

                      {/* Nutrition Facts */}
                      <div>
                        <h5 className="font-medium text-gray-900 mb-2">Nutrition (per 100g):</h5>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                          <div className="bg-gray-50 px-3 py-2 rounded">
                            <div className="text-gray-500">Protein</div>
                            <div className="font-medium">{rec.recipe.protein_g}g</div>
                          </div>
                          <div className="bg-gray-50 px-3 py-2 rounded">
                            <div className="text-gray-500">Iron</div>
                            <div className="font-medium">{rec.recipe.iron_mg}mg</div>
                          </div>
                          <div className="bg-gray-50 px-3 py-2 rounded">
                            <div className="text-gray-500">Calcium</div>
                            <div className="font-medium">{rec.recipe.calcium_mg}mg</div>
                          </div>
                          <div className="bg-gray-50 px-3 py-2 rounded">
                            <div className="text-gray-500">Fiber</div>
                            <div className="font-medium">{rec.recipe.fiber_g}g</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Nutritional Alternatives Section */}
      {alternatives && Object.keys(alternatives).length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle size={20} className="text-orange-600" />
            Nutritional Alternatives
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Since {baby?.name} doesn't like some ingredients, here are nutritionally similar alternatives:
          </p>

          <div className="space-y-3">
            {Object.entries(alternatives).map(([ingredient, data]) => (
              <div key={ingredient} className="bg-orange-50 border border-orange-200 rounded-lg">
                <button
                  onClick={() => toggleAlternative(ingredient)}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-orange-100 transition-colors"
                >
                  <div className="text-left">
                    <div className="font-medium text-gray-900 capitalize">
                      Alternatives for {ingredient}
                    </div>
                    <div className="text-sm text-gray-600">
                      {data.nutrition_importance}
                    </div>
                  </div>
                  {expandedAlternatives[ingredient] ? (
                    <ChevronUp size={20} className="text-gray-400" />
                  ) : (
                    <ChevronDown size={20} className="text-gray-400" />
                  )}
                </button>

                {expandedAlternatives[ingredient] && (
                  <div className="px-4 pb-4 space-y-3">
                    {/* LLM Suggestions */}
                    {data.llm_suggestions && data.llm_suggestions.length > 0 && (
                      <div>
                        <h5 className="text-sm font-medium text-gray-900 mb-2">
                          AI Suggestions:
                        </h5>
                        <div className="space-y-2">
                          {data.llm_suggestions.map((suggestion, i) => (
                            <div key={i} className="bg-white rounded p-3 text-sm">
                              <div className="font-medium text-gray-900 mb-1">
                                {suggestion.ingredient}
                              </div>
                              <div className="text-gray-700 mb-1">{suggestion.reason}</div>
                              <div className="text-gray-600 italic">
                                💡 {suggestion.preparation_tip}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Alternative Recipes */}
                    {data.alternative_recipes && data.alternative_recipes.length > 0 && (
                      <div>
                        <h5 className="text-sm font-medium text-gray-900 mb-2">
                          Similar Recipes:
                        </h5>
                        <div className="space-y-2">
                          {data.alternative_recipes.map((alt, i) => (
                            <div key={i} className="bg-white rounded p-3 text-sm">
                              <div className="font-medium text-gray-900">
                                {alt.recipe.name}
                              </div>
                              <div className="text-gray-600 text-xs mt-1">
                                Uses {alt.alternative_ingredient} • {Math.round(alt.similarity_score * 100)}% similar nutrition
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Retry Suggestions */}
      {retry_suggestions && retry_suggestions.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <RefreshCw size={20} className="text-blue-600" />
            Try Again Suggestions
          </h3>
          
          <div className="space-y-3">
            {retry_suggestions.map((suggestion, index) => (
              <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="font-medium text-gray-900 mb-2 capitalize">
                  {suggestion.ingredient}
                </div>
                <p className="text-sm text-gray-700 mb-3">
                  {suggestion.strategy?.specific_suggestion || suggestion.strategy?.strategy}
                </p>
                
                {suggestion.different_preparations && suggestion.different_preparations.length > 0 && (
                  <div className="text-sm text-gray-600">
                    <div className="font-medium mb-1">Different ways to try:</div>
                    <ul className="list-disc list-inside space-y-1 ml-2">
                      {suggestion.different_preparations.map((prep, i) => (
                        <li key={i}>{prep}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}