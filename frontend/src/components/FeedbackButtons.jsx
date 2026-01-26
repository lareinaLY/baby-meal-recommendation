/**
 * Feedback Buttons Component
 * Quick feedback interface for recommendations
 */
import { useState } from 'react';
import { ThumbsUp, ThumbsDown, Check } from 'lucide-react';
import { recommendationAPI } from '../services/api';

export default function FeedbackButtons({ baby, recipe, onFeedbackSubmitted }) {
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleFeedback = async (accepted, rating) => {
    setSubmitting(true);
    
    try {
      await recommendationAPI.submitFeedback({
        baby_id: baby.id,
        recipe_id: recipe.id,
        rating: rating,
        accepted: accepted,
        prepared: accepted, // Assume prepared if accepted
        baby_liked: accepted ? true : null,
        comments: accepted ? 'Accepted via UI' : 'Rejected via UI',
        rejection_reason: accepted ? null : 'baby_refused'
      });

      setSubmitted(true);
      
      // Notify parent component
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted();
      }

      // Reset after 2 seconds
      setTimeout(() => setSubmitted(false), 2000);
      
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      alert('Failed to submit feedback: ' + error.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-800 rounded-lg">
        <Check size={16} />
        <span className="text-sm font-medium">Feedback saved!</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => handleFeedback(true, 5)}
        disabled={submitting}
        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-50 border-2 border-green-200 text-green-700 rounded-lg hover:bg-green-100 transition-colors disabled:opacity-50"
      >
        <ThumbsUp size={16} />
        <span className="font-medium">Love it</span>
      </button>
      
      <button
        onClick={() => handleFeedback(true, 3.5)}
        disabled={submitting}
        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-50 border-2 border-blue-200 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors disabled:opacity-50"
      >
        <Check size={16} />
        <span className="font-medium">It's OK</span>
      </button>
      
      <button
        onClick={() => handleFeedback(false, 2)}
        disabled={submitting}
        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-50 border-2 border-red-200 text-red-700 rounded-lg hover:bg-red-100 transition-colors disabled:opacity-50"
      >
        <ThumbsDown size={16} />
        <span className="font-medium">Don't like</span>
      </button>
    </div>
  );
}