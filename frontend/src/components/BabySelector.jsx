/**
 * Baby Selector Component
 * Allows parent to select which baby profile to use
 */
import { Baby, ChevronDown } from 'lucide-react';
import { useEffect, useState } from 'react';
import { babyAPI } from '../services/api';

export default function BabySelector({ selectedBaby, onBabyChange }) {
    const [babies, setBabies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isOpen, setIsOpen] = useState(false);

    useEffect(() => {
        loadBabies();
    }, []);

    const loadBabies = async () => {
        try {
            const data = await babyAPI.getAll();
            setBabies(data);

            // Auto-select first baby if none selected
            if (data.length > 0 && !selectedBaby) {
                onBabyChange(data[0]);
            }

            setLoading(false);
        } catch (error) {
            console.error('Failed to load babies:', error);
            setLoading(false);
        }
    };

    const handleSelect = (baby) => {
        onBabyChange(baby);
        setIsOpen(false);
    };

    if (loading) {
        return (
            <div className="flex items-center gap-2 text-gray-500">
                <Baby size={20} />
                <span>Loading babies...</span>
            </div>
        );
    }

    if (babies.length === 0) {
        return (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800">
                    No baby profiles found. Create one in Swagger UI:
                    <a
                        href="http://localhost:8000/docs#/Babies/create_baby_api_v1_babies__post"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-2 text-blue-600 hover:underline"
                    >
                        Create Baby →
                    </a>
                </p>
            </div>
        );
    }

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-3 bg-white border border-gray-300 rounded-lg px-4 py-3 hover:border-primary-500 transition-colors w-full md:w-auto"
            >
                <Baby className="text-primary-600" size={24} />
                <div className="flex-1 text-left">
                    <div className="font-semibold text-gray-900">
                        {selectedBaby?.name || 'Select Baby'}
                    </div>
                    {selectedBaby && (
                        <div className="text-sm text-gray-500">
                            {selectedBaby.age_months} months • {selectedBaby.age_stage}
                        </div>
                    )}
                </div>
                <ChevronDown
                    size={20}
                    className={`text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
                />
            </button>

            {/* Dropdown */}
            {isOpen && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-10 max-h-64 overflow-y-auto">
                    {babies.map((baby) => (
                        <button
                            key={baby.id}
                            onClick={() => handleSelect(baby)}
                            className={`w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors ${selectedBaby?.id === baby.id ? 'bg-primary-50' : ''
                                }`}
                        >
                            <div className="font-medium text-gray-900">{baby.name}</div>
                            <div className="text-sm text-gray-500">
                                {baby.age_months} months • {baby.age_stage}
                            </div>
                            {baby.allergies && baby.allergies.length > 0 && (
                                <div className="text-xs text-red-600 mt-1">
                                    Allergies: {baby.allergies.join(', ')}
                                </div>
                            )}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}