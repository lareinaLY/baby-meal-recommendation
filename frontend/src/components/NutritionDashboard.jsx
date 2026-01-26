/**
 * Nutrition Dashboard Component
 * Visualizes nutrition tracking with charts and AI insights
 */
import { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { TrendingUp, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';
import { recommendationAPI } from '../services/api';

const COLORS = {
  adequate: '#10b981',    // green
  deficient: '#ef4444',   // red
  excessive: '#f59e0b',   // orange
};

export default function NutritionDashboard({ baby }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [days, setDays] = useState(7);

  useEffect(() => {
    if (baby) {
      loadAnalysis();
    }
  }, [baby, days]);

  const loadAnalysis = async () => {
    if (!baby) return;

    setLoading(true);
    try {
      const data = await recommendationAPI.getNutritionAnalysis(baby.id, days);
      console.log('Nutrition analysis:', data);
      setAnalysis(data);
    } catch (error) {
      console.error('Failed to load nutrition analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!baby) {
    return (
      <div className="text-center py-12 text-gray-500">
        <TrendingUp size={48} className="mx-auto mb-4 text-gray-400" />
        <p>Select a baby to view nutrition analysis</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Analyzing nutrition data...</p>
        </div>
      </div>
    );
  }

  if (!analysis || analysis.total_meals === 0) {
    return (
      <div className="text-center py-12">
        <AlertTriangle size={48} className="mx-auto mb-4 text-gray-400" />
        <p className="text-gray-600 mb-4">
          No feeding data for the past {days} days.
        </p>
        <p className="text-sm text-gray-500">
          Submit feedback on recommended recipes to see nutrition tracking.
        </p>
      </div>
    );
  }

  // Prepare chart data - separate into two groups by magnitude
  const nutrientData = Object.keys(analysis.nutrient_totals).map(nutrient => {
    const total = analysis.nutrient_totals[nutrient];
    const target = analysis.nutrient_targets[nutrient];
    const percentage = (total / target) * 100;
    const status = percentage < 70 ? 'deficient' : percentage > 150 ? 'excessive' : 'adequate';

    return {
      name: nutrient.replace('_', ' ').replace('mg', ' (mg)').replace('g', ' (g)').replace('mcg', ' (mcg)'),
      actual: Math.round(total * 10) / 10,
      target: Math.round(target * 10) / 10,
      percentage: Math.round(percentage),
      status
    };
  });

  // Split nutrients by magnitude for better visualization
  const largeNutrients = nutrientData.filter(n => n.target >= 100);
  const smallNutrients = nutrientData.filter(n => n.target < 100);

  // Pie chart data for nutrient distribution
  const pieData = [
    { name: 'Protein', value: analysis.nutrient_totals.protein_g || 0, color: '#3b82f6' },
    { name: 'Iron', value: (analysis.nutrient_totals.iron_mg || 0) * 5, color: '#ef4444' },
    { name: 'Calcium', value: (analysis.nutrient_totals.calcium_mg || 0) / 10, color: '#10b981' },
    { name: 'Fiber', value: analysis.nutrient_totals.fiber_g || 0, color: '#f59e0b' },
  ].filter(item => item.value > 0);

  return (
    <div className="space-y-6">
      {/* Header with Time Period Selector */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900 flex items-center gap-2">
            <TrendingUp className="text-primary-600" size={24} />
            Nutrition Analysis for {baby.name}
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            {analysis.total_meals} meals tracked in the past {days} days
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value={3}>Last 3 days</option>
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
          </select>

          <button
            onClick={loadAnalysis}
            className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            title="Refresh analysis"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* AI Assessment */}
      {analysis.assessment && (
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
            🤖 AI Nutrition Insights
          </h3>
          <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-line">
            {analysis.assessment}
          </p>
        </div>
      )}

      {/* Status Badges */}
      <div className="flex flex-wrap gap-3">
        {analysis.deficiencies && analysis.deficiencies.length > 0 && (
          <div className="flex items-center gap-2 px-4 py-2 bg-red-50 border border-red-200 rounded-lg">
            <AlertTriangle size={16} className="text-red-600" />
            <span className="text-sm font-medium text-red-800">
              {analysis.deficiencies.length} nutrient{analysis.deficiencies.length > 1 ? 's' : ''} below target
            </span>
          </div>
        )}
        
        {(!analysis.deficiencies || analysis.deficiencies.length === 0) && (
          <div className="flex items-center gap-2 px-4 py-2 bg-green-50 border border-green-200 rounded-lg">
            <CheckCircle size={16} className="text-green-600" />
            <span className="text-sm font-medium text-green-800">
              All nutrients adequate
            </span>
          </div>
        )}

        {analysis.excesses && analysis.excesses.length > 0 && (
          <div className="flex items-center gap-2 px-4 py-2 bg-orange-50 border border-orange-200 rounded-lg">
            <AlertTriangle size={16} className="text-orange-600" />
            <span className="text-sm font-medium text-orange-800">
              {analysis.excesses.length} nutrient{analysis.excesses.length > 1 ? 's' : ''} excessive
            </span>
          </div>
        )}
      </div>

      {/* Bar Charts: Actual vs Target - Split by magnitude */}
      {largeNutrients.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Major Nutrients (Calcium, Vitamin B12)</h3>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart 
              data={largeNutrients}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={0}
                textAnchor="middle"
                height={60}
                interval={0}
                tick={{ fontSize: 11 }}
              />
              <YAxis />
              <Tooltip 
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-lg">
                        <p className="font-medium text-gray-900">{data.name}</p>
                        <p className="text-sm text-gray-600">Actual: {data.actual}</p>
                        <p className="text-sm text-gray-600">Target: {data.target}</p>
                        <p className={`text-sm font-medium ${
                          data.status === 'deficient' ? 'text-red-600' :
                          data.status === 'excessive' ? 'text-orange-600' :
                          'text-green-600'
                        }`}>
                          {data.percentage}% of target
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend />
              <Bar dataKey="actual" fill="#0ea5e9" name="Actual Intake" />
              <Bar dataKey="target" fill="#e5e7eb" name="Target" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {smallNutrients.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Trace Nutrients (Iron, Protein, Fiber)</h3>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart 
              data={smallNutrients}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={0}
                textAnchor="middle"
                height={60}
                interval={0}
                tick={{ fontSize: 11 }}
              />
              <YAxis />
              <Tooltip 
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-lg">
                        <p className="font-medium text-gray-900">{data.name}</p>
                        <p className="text-sm text-gray-600">Actual: {data.actual}</p>
                        <p className="text-sm text-gray-600">Target: {data.target}</p>
                        <p className={`text-sm font-medium ${
                          data.status === 'deficient' ? 'text-red-600' :
                          data.status === 'excessive' ? 'text-orange-600' :
                          'text-green-600'
                        }`}>
                          {data.percentage}% of target
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend />
              <Bar dataKey="actual" fill="#0ea5e9" name="Actual Intake" />
              <Bar dataKey="target" fill="#e5e7eb" name="Target" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Pie Chart: Nutrient Distribution */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Nutrient Distribution</h3>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Detailed Nutrient List */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Detailed Breakdown</h3>
        <div className="space-y-3">
          {nutrientData.map((nutrient, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-gray-900 capitalize">
                    {nutrient.name}
                  </span>
                  {analysis.deficiencies?.includes(nutrient.name.split(' ')[0].replace(' ', '_')) && (
                    <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">
                      Low
                    </span>
                  )}
                  {analysis.excesses?.includes(nutrient.name.split(' ')[0].replace(' ', '_')) && (
                    <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded-full">
                      High
                    </span>
                  )}
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      nutrient.status === 'deficient' ? 'bg-red-500' :
                      nutrient.status === 'excessive' ? 'bg-orange-500' :
                      'bg-green-500'
                    }`}
                    style={{ width: `${Math.min(nutrient.percentage, 100)}%` }}
                  />
                </div>
              </div>
              <div className="ml-4 text-right">
                <div className="font-medium text-gray-900">
                  {nutrient.actual} / {nutrient.target}
                </div>
                <div className={`text-sm ${
                  nutrient.status === 'deficient' ? 'text-red-600' :
                  nutrient.status === 'excessive' ? 'text-orange-600' :
                  'text-green-600'
                }`}>
                  {nutrient.percentage}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}