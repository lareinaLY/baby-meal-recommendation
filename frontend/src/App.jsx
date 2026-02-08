/**
 * Baby Meal AI Assistant - Main Application
 * Complete version with Authentication, Chat, Recommendations, and Nutrition Analysis
 */
import { AlertCircle, LogOut, MessageSquare, RefreshCw, Sparkles, TrendingUp } from 'lucide-react';
import { useEffect, useState } from 'react';
import BabySelector from './components/BabySelector';
import ChatInterface from './components/ChatInterface';
import Login from './components/Login';
import NutritionDashboard from './components/NutritionDashboard';
import SmartRecommendations from './components/SmartRecommendations';
import { recommendationAPI } from './services/api';
import authService from './services/auth';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [selectedBaby, setSelectedBaby] = useState(null);
  const [activeTab, setActiveTab] = useState('chat');
  const [recommendations, setRecommendations] = useState(null);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [aiStatus, setAiStatus] = useState(null);

  // Chat state (lifted to prevent loss on tab switch)
  const [chatMessages, setChatMessages] = useState([]);

  // Check authentication on mount
  useEffect(() => {
    const authenticated = authService.isAuthenticated();
    setIsAuthenticated(authenticated);

    if (authenticated) {
      const user = authService.getUser();
      setCurrentUser(user);
    }
  }, []);

  // Check AI features status on mount
  useEffect(() => {
    if (isAuthenticated) {
      checkAIStatus();
    }
  }, [isAuthenticated]);

  // Initialize welcome message when baby is selected
  useEffect(() => {
    if (selectedBaby && chatMessages.length === 0) {
      const welcomeMsg = {
        role: 'assistant',
        content: `Hi! I'm your AI nutrition assistant for ${selectedBaby.name}. I know ${selectedBaby.name} is ${selectedBaby.age_months} months old${selectedBaby.liked_ingredients?.length > 0 ? ` and enjoys ${selectedBaby.liked_ingredients.join(', ')}` : ''}. How can I help you today?`,
        timestamp: new Date(),
      };
      setChatMessages([welcomeMsg]);
    }
  }, [selectedBaby]);

  const checkAIStatus = async () => {
    try {
      const status = await recommendationAPI.getStatus();
      setAiStatus(status);
      console.log('AI Status:', status);
    } catch (error) {
      console.error('Failed to check AI status:', error);
    }
  };

  const loadSmartRecommendations = async () => {
    if (!selectedBaby) return;

    setLoadingRecs(true);
    try {
      console.log('Loading SMART recommendations for baby:', selectedBaby.id);

      // Use smart API for AI-enhanced recommendations
      const data = await recommendationAPI.getSmart(selectedBaby.id, 5);

      console.log('Smart recommendations received:', data);
      console.log('Primary count:', data.primary_recommendations?.length);

      setRecommendations(data);

    } catch (error) {
      console.error('Failed to load smart recommendations:', error);

      // Fallback to basic recommendations if smart fails
      try {
        console.log('Falling back to basic recommendations...');
        const basicRecs = await recommendationAPI.getBasic(selectedBaby.id, 5);

        // Convert to smart format
        const fallbackData = {
          primary_recommendations: basicRecs.map(recipe => ({
            recipe: recipe,
            score: recipe.recommendation_score,
            explanation: recipe.match_reason,
            is_retry: false,
            penalty_applied: false,
            original_score: recipe.recommendation_score,
            nutritional_highlights: null
          })),
          alternatives: {},
          retry_suggestions: [],
          overall_explanation: `Showing basic recommendations for ${selectedBaby.name}. Smart features temporarily unavailable.`,
          nutrition_analysis: null
        };

        setRecommendations(fallbackData);
        console.log('Using fallback basic recommendations');

      } catch (fallbackError) {
        console.error('Fallback also failed:', fallbackError);
        alert('Failed to get recommendations: ' + error.message);
      }
    } finally {
      setLoadingRecs(false);
    }
  };

  const handleFeedbackSubmitted = () => {
    console.log('Feedback submitted, you may want to refresh nutrition analysis');
  };

  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(false);
    setCurrentUser(null);
    setSelectedBaby(null);
    setChatMessages([]);
    setRecommendations(null);
  };

  // Show login if not authenticated
  if (!isAuthenticated) {
    return <Login onLoginSuccess={() => {
      setIsAuthenticated(true);
      const user = authService.getUser();
      setCurrentUser(user);
    }} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                🍼 Baby Meal AI Assistant
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                Personalized nutrition guidance powered by AI
              </p>
            </div>

            {/* User Info & AI Status */}
            <div className="flex items-center gap-4">
              {/* AI Status Indicator */}
              {aiStatus && (
                <div className="flex items-center gap-2">
                  {aiStatus.smart_features_available && aiStatus.openai_api_key_configured ? (
                    <div className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                      <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse" />
                      AI Active
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm">
                      <AlertCircle size={14} />
                      AI Limited
                    </div>
                  )}
                </div>
              )}

              {/* User Menu */}
              {currentUser && (
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {currentUser.email}
                    </div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="px-3 py-2 text-sm text-gray-700 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors flex items-center gap-2"
                    title="Logout"
                  >
                    <LogOut size={16} />
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Baby Selector */}
          <div className="mt-4">
            <BabySelector
              selectedBaby={selectedBaby}
              onBabyChange={setSelectedBaby}
            />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {selectedBaby ? (
          <>
            {/* Tab Navigation */}
            <div className="flex gap-2 mb-6 border-b border-gray-200">
              <button
                onClick={() => setActiveTab('chat')}
                className={`px-6 py-3 font-medium transition-colors flex items-center gap-2 border-b-2 ${activeTab === 'chat'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
              >
                <MessageSquare size={20} />
                Chat Assistant
              </button>

              <button
                onClick={() => {
                  setActiveTab('recommendations');
                  if (!recommendations) {
                    loadSmartRecommendations();
                  }
                }}
                className={`px-6 py-3 font-medium transition-colors flex items-center gap-2 border-b-2 ${activeTab === 'recommendations'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
              >
                <Sparkles size={20} />
                Smart Recommendations
              </button>

              <button
                onClick={() => setActiveTab('nutrition')}
                className={`px-6 py-3 font-medium transition-colors flex items-center gap-2 border-b-2 ${activeTab === 'nutrition'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
              >
                <TrendingUp size={20} />
                Nutrition Analysis
              </button>
            </div>

            {/* Tab Content */}
            <div className="bg-white rounded-lg shadow-sm" style={{ height: 'calc(100vh - 280px)' }}>
              {activeTab === 'chat' ? (
                <ChatInterface
                  baby={selectedBaby}
                  messages={chatMessages}
                  setMessages={setChatMessages}
                />
              ) : activeTab === 'recommendations' ? (
                <div className="h-full overflow-y-auto p-6">
                  {loadingRecs ? (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
                        <p className="text-gray-600">Getting AI recommendations...</p>
                      </div>
                    </div>
                  ) : !recommendations ? (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <Sparkles size={48} className="mx-auto mb-4 text-gray-400" />
                        <button
                          onClick={loadSmartRecommendations}
                          className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                        >
                          Get AI Recommendations
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-semibold text-gray-900">
                          Personalized for {selectedBaby.name}
                        </h2>
                        <button
                          onClick={loadSmartRecommendations}
                          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm flex items-center gap-2"
                        >
                          <RefreshCw size={16} />
                          Refresh
                        </button>
                      </div>
                      <SmartRecommendations
                        recommendations={recommendations}
                        baby={selectedBaby}
                        onFeedbackSubmitted={handleFeedbackSubmitted}
                      />
                    </>
                  )}
                </div>
              ) : (
                <div className="h-full overflow-y-auto p-6">
                  <NutritionDashboard baby={selectedBaby} />
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center" style={{ height: 'calc(100vh - 200px)' }}>
            <div className="text-center">
              <div className="text-6xl mb-4">👶</div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Welcome to Baby Meal AI Assistant
              </h2>
              <p className="text-gray-600 mb-4">
                Select or create a baby profile to get started
              </p>
              <p className="text-sm text-gray-500">
                Create babies in{' '}
                <a
                  href="http://localhost:8000/docs#/Babies/create_baby_api_v1_babies__post"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  Swagger UI
                </a>
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="text-center py-6 text-sm text-gray-500">
        <p>
          Powered by OpenAI GPT-4 • Built with React + FastAPI + PostgreSQL
        </p>
      </footer>
    </div>
  );
}

export default App;