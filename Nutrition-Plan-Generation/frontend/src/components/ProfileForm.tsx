import React, { useState } from 'react';
import type { GenerateNutritionRequest, GoalType, ActivityLevel, DietType, GenderType, MealGenerationMode } from '../types';
import { Play, Loader2, Sparkles, User, Target, Utensils, AlertTriangle, Database, Bot, Layers } from 'lucide-react';

interface ProfileFormProps {
  onSubmit: (request: GenerateNutritionRequest) => void;
  isLoading: boolean;
}

const COMMON_ALLERGIES = ['dairy', 'nuts', 'gluten', 'seafood', 'eggs', 'soy'];
const COMMON_PREFERENCES = ['chicken', 'fish', 'oats', 'rice', 'avocado', 'eggs', 'olive oil', 'broccoli'];

export const ProfileForm: React.FC<ProfileFormProps> = ({ onSubmit, isLoading }) => {
  const [age, setAge] = useState<number>(28);
  const [gender, setGender] = useState<GenderType>('male');
  const [heightCm, setHeightCm] = useState<number>(178);
  const [weightKg, setWeightKg] = useState<number>(76);
  const [goal, setGoal] = useState<GoalType>('fat_loss');
  const [activityLevel, setActivityLevel] = useState<ActivityLevel>('moderate');
  const [dietType, setDietType] = useState<DietType>('normal');
  const [allergies, setAllergies] = useState<string[]>([]);
  const [preferences, setPreferences] = useState<string[]>(['chicken', 'oats']);
  const [notes, setNotes] = useState<string>('Prefer quick prep meals during weekdays.');
  const [generationMode, setGenerationMode] = useState<MealGenerationMode>('llm_arabic');

  const toggleAllergy = (item: string) => {
    setAllergies(prev => prev.includes(item) ? prev.filter(a => a !== item) : [...prev, item]);
  };

  const togglePreference = (item: string) => {
    setPreferences(prev => prev.includes(item) ? prev.filter(p => p !== item) : [...prev, item]);
  };

  const handlePreset = (
    pAge: number, pGen: GenderType, pHeight: number, pWeight: number,
    pGoal: GoalType, pAct: ActivityLevel, pDiet: DietType, pAller: string[], pPref: string[], pNotes: string
  ) => {
    setAge(pAge); setGender(pGen); setHeightCm(pHeight); setWeightKg(pWeight);
    setGoal(pGoal); setActivityLevel(pAct); setDietType(pDiet);
    setAllergies(pAller); setPreferences(pPref); setNotes(pNotes);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      age,
      gender,
      height_cm: heightCm,
      weight_kg: weightKg,
      goal,
      activity_level: activityLevel,
      diet_type: dietType,
      preferences,
      allergies,
      additional_notes: notes,
      meal_generation_mode: generationMode,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="glass-card" style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <User size={20} className="gradient-text" /> Patient Profile &amp; Clinical Goals
        </h2>
        <span className="badge badge-green">AI Profile Node</span>
      </div>

      {/* Quick Demo Presets */}
      <div style={{ marginBottom: '20px', padding: '12px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          ⚡ One-Click Demo Profiles
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
            onClick={() => handlePreset(26, 'male', 180, 82, 'fat_loss', 'moderate', 'normal', [], ['chicken', 'oats', 'eggs'], 'High protein, easy prep meals.')}
          >
            🔥 Male Fat Loss (1200-1800 kcal)
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
            onClick={() => handlePreset(24, 'female', 165, 58, 'muscle_gain', 'very_active', 'high_protein', ['dairy'], ['fish', 'olive oil', 'avocado'], 'No dairy products.')}
          >
            💪 Female Muscle Gain (Dairy Free)
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
            onClick={() => handlePreset(32, 'male', 175, 70, 'maintenance', 'lightly_active', 'vegan', [], ['oats', 'rice', 'broccoli'], '100% plant based foods only.')}
          >
            🌱 Vegan Maintenance
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ padding: '6px 12px', fontSize: '0.8rem', borderColor: 'rgba(245,158,11,0.4)', color: '#fbbf24' }}
            onClick={() => { handlePreset(30, 'male', 178, 80, 'fat_loss', 'moderate', 'normal', [], ['chicken'], 'Prefer authentic Egyptian foods.'); setGenerationMode('llm_arabic_parquet'); }}
          >
            🗄️ مصري — Parquet Arabic
          </button>
        </div>
      </div>

      {/* Biometrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
        <div className="input-group" style={{ margin: 0 }}>
          <label className="input-label">Age (years)</label>
          <input type="number" min="15" max="100" className="form-input" value={age} onChange={e => setAge(Number(e.target.value))} required />
        </div>
        <div className="input-group" style={{ margin: 0 }}>
          <label className="input-label">Gender</label>
          <select className="form-select" value={gender} onChange={e => setGender(e.target.value as GenderType)}>
            <option value="male">Male</option>
            <option value="female">Female</option>
          </select>
        </div>
        <div className="input-group" style={{ margin: 0 }}>
          <label className="input-label">Height (cm)</label>
          <input type="number" min="120" max="220" className="form-input" value={heightCm} onChange={e => setHeightCm(Number(e.target.value))} required />
        </div>
        <div className="input-group" style={{ margin: 0 }}>
          <label className="input-label">Weight (kg)</label>
          <input type="number" min="35" max="200" className="form-input" value={weightKg} onChange={e => setWeightKg(Number(e.target.value))} required />
        </div>
      </div>

      {/* Goal & Activity */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
        <div className="input-group" style={{ margin: 0 }}>
          <label className="input-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Target size={14} /> Nutrition Goal
          </label>
          <select className="form-select" value={goal} onChange={e => setGoal(e.target.value as GoalType)}>
            <option value="fat_loss">Fat Loss (-500 kcal)</option>
            <option value="weight_loss">Weight Loss (-300 kcal)</option>
            <option value="muscle_gain">Muscle Gain (+300 kcal)</option>
            <option value="bulking">Bulking (+500 kcal)</option>
            <option value="maintenance">Maintenance</option>
            <option value="recomposition">Body Recomposition</option>
          </select>
        </div>
        <div className="input-group" style={{ margin: 0 }}>
          <label className="input-label">Activity Level</label>
          <select className="form-select" value={activityLevel} onChange={e => setActivityLevel(e.target.value as ActivityLevel)}>
            <option value="sedentary">Sedentary (Little or no exercise)</option>
            <option value="lightly_active">Lightly Active (Exercise 1-3 days/week)</option>
            <option value="moderate">Moderate (Exercise 3-5 days/week)</option>
            <option value="very_active">Very Active (Hard exercise/physical job)</option>
            <option value="extra_active">Extra Active (Athlete/twice daily training)</option>
          </select>
        </div>
      </div>

      {/* Diet Type */}
      <div className="input-group">
        <label className="input-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Utensils size={14} /> Dietary Preference
        </label>
        <select className="form-select" value={dietType} onChange={e => setDietType(e.target.value as DietType)}>
          <option value="normal">Normal / Balanced Diet</option>
          <option value="high_protein">High Protein Diet</option>
          <option value="vegetarian">Vegetarian (No meat/seafood)</option>
          <option value="vegan">Vegan (No animal products)</option>
          <option value="keto">Keto / Low Carb</option>
        </select>
      </div>

      {/* Allergies */}
      <div className="input-group">
        <label className="input-label" style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#fb7185' }}>
          <AlertTriangle size={14} /> Allergies / Exclusions
        </label>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '4px' }}>
          {COMMON_ALLERGIES.map(item => (
            <button
              key={item}
              type="button"
              onClick={() => toggleAllergy(item)}
              style={{
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                background: allergies.includes(item) ? 'rgba(244, 63, 94, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                color: allergies.includes(item) ? '#fb7185' : 'var(--text-muted)',
                border: allergies.includes(item) ? '1px solid rgba(244, 63, 94, 0.5)' : '1px solid var(--border-color)',
                transition: 'all 0.2s ease'
              }}
            >
              {allergies.includes(item) ? `🚫 ${item}` : `+ ${item}`}
            </button>
          ))}
        </div>
      </div>

      {/* Preferred Foods */}
      <div className="input-group">
        <label className="input-label">Food Preferences (Ranked Higher in Retrieval)</label>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '4px' }}>
          {COMMON_PREFERENCES.map(item => (
            <button
              key={item}
              type="button"
              onClick={() => togglePreference(item)}
              style={{
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                background: preferences.includes(item) ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.04)',
                color: preferences.includes(item) ? '#34d399' : 'var(--text-muted)',
                border: preferences.includes(item) ? '1px solid rgba(16, 185, 129, 0.5)' : '1px solid var(--border-color)',
                transition: 'all 0.2s ease'
              }}
            >
              {preferences.includes(item) ? `✓ ${item}` : `+ ${item}`}
            </button>
          ))}
        </div>
      </div>

      {/* Notes */}
      <div className="input-group">
        <label className="input-label">Clinical / Lifestyle Notes</label>
        <textarea
          rows={2}
          className="form-textarea"
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="e.g. Prefer high-protein breakfasts, fast prep dinners..."
        />
      </div>

      {/* Generation Mode Toggle */}
      <div className="input-group">
        <label className="input-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          ⚙️ Generation Mode
        </label>

        {/* 3-column card selector */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', marginTop: '4px' }}>

          {/* Dataset Mode */}
          <button
            type="button"
            onClick={() => setGenerationMode('dataset')}
            style={{
              padding: '14px 8px',
              borderRadius: '12px',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '5px',
              transition: 'all 0.25s ease',
              background: generationMode === 'dataset'
                ? 'linear-gradient(135deg, rgba(16,185,129,0.22), rgba(5,150,105,0.12))'
                : 'rgba(255,255,255,0.03)',
              border: generationMode === 'dataset'
                ? '1.5px solid rgba(16,185,129,0.65)'
                : '1.5px solid var(--border-color)',
              boxShadow: generationMode === 'dataset' ? '0 0 16px rgba(16,185,129,0.15)' : 'none',
            }}
          >
            <Database size={18} color={generationMode === 'dataset' ? '#34d399' : 'var(--text-muted)'} />
            <span style={{
              fontSize: '0.78rem',
              fontWeight: 700,
              color: generationMode === 'dataset' ? '#34d399' : 'var(--text-muted)'
            }}>Dataset</span>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textAlign: 'center', lineHeight: 1.3 }}>
              Excel food DB
            </span>
          </button>

          {/* LLM Arabic Mode */}
          <button
            type="button"
            onClick={() => setGenerationMode('llm_arabic')}
            style={{
              padding: '14px 8px',
              borderRadius: '12px',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '5px',
              transition: 'all 0.25s ease',
              background: generationMode === 'llm_arabic'
                ? 'linear-gradient(135deg, rgba(139,92,246,0.22), rgba(109,40,217,0.12))'
                : 'rgba(255,255,255,0.03)',
              border: generationMode === 'llm_arabic'
                ? '1.5px solid rgba(139,92,246,0.65)'
                : '1.5px solid var(--border-color)',
              boxShadow: generationMode === 'llm_arabic' ? '0 0 16px rgba(139,92,246,0.18)' : 'none',
            }}
          >
            <Bot size={18} color={generationMode === 'llm_arabic' ? '#a78bfa' : 'var(--text-muted)'} />
            <span style={{
              fontSize: '0.78rem',
              fontWeight: 700,
              color: generationMode === 'llm_arabic' ? '#a78bfa' : 'var(--text-muted)'
            }}>🇪🇬 LLM Arabic</span>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textAlign: 'center', lineHeight: 1.3 }}>
              AI free-form Arabic
            </span>
          </button>

          {/* Parquet Arabic Mode — NEW */}
          <button
            type="button"
            onClick={() => setGenerationMode('llm_arabic_parquet')}
            style={{
              padding: '14px 8px',
              borderRadius: '12px',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '5px',
              transition: 'all 0.25s ease',
              position: 'relative',
              background: generationMode === 'llm_arabic_parquet'
                ? 'linear-gradient(135deg, rgba(245,158,11,0.22), rgba(234,88,12,0.12))'
                : 'rgba(255,255,255,0.03)',
              border: generationMode === 'llm_arabic_parquet'
                ? '1.5px solid rgba(245,158,11,0.65)'
                : '1.5px solid var(--border-color)',
              boxShadow: generationMode === 'llm_arabic_parquet' ? '0 0 18px rgba(245,158,11,0.2)' : 'none',
            }}
          >
            {/* NEW badge */}
            <span style={{
              position: 'absolute',
              top: '-8px',
              right: '-6px',
              background: 'linear-gradient(135deg, #f59e0b, #ef4444)',
              color: 'white',
              fontSize: '0.58rem',
              fontWeight: 800,
              padding: '2px 6px',
              borderRadius: '20px',
              letterSpacing: '0.04em',
            }}>NEW</span>
            <Layers size={18} color={generationMode === 'llm_arabic_parquet' ? '#fbbf24' : 'var(--text-muted)'} />
            <span style={{
              fontSize: '0.78rem',
              fontWeight: 700,
              color: generationMode === 'llm_arabic_parquet' ? '#fbbf24' : 'var(--text-muted)'
            }}>🗄️ Parquet + AI</span>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textAlign: 'center', lineHeight: 1.3 }}>
              Real foods + Arabic LLM
            </span>
          </button>
        </div>

        {/* Context banners */}
        {generationMode === 'dataset' && (
          <p style={{
            marginTop: '8px',
            fontSize: '0.78rem',
            color: '#34d399',
            background: 'rgba(16,185,129,0.08)',
            borderRadius: '8px',
            padding: '8px 12px',
            border: '1px solid rgba(16,185,129,0.2)',
          }}>
            🗂️ Retrieves from the Egyptian food Excel database → ranks by allergens, diet type & preferences → English LLM composes a single validated plan.
          </p>
        )}
        {generationMode === 'llm_arabic' && (
          <p style={{
            marginTop: '8px',
            fontSize: '0.78rem',
            color: '#a78bfa',
            background: 'rgba(139,92,246,0.08)',
            borderRadius: '8px',
            padding: '8px 12px',
            border: '1px solid rgba(139,92,246,0.2)',
          }}>
            🤖 The AI freely creates authentic Egyptian meals with Arabic names (فول، كشري، ملوخية...) tailored to your macro targets — no database constraints. Generates <strong>3 diverse options</strong> per slot.
          </p>
        )}
        {generationMode === 'llm_arabic_parquet' && (
          <p style={{
            marginTop: '8px',
            fontSize: '0.78rem',
            color: '#fbbf24',
            background: 'rgba(245,158,11,0.08)',
            borderRadius: '8px',
            padding: '8px 12px',
            border: '1px solid rgba(245,158,11,0.25)',
          }}>
            🗄️ <strong>Best of both worlds:</strong> Filters 793 real foods from the parquet dataset per meal slot (goal fit, allergens, diet, slot type) then sends those real Arabic-named foods to the LLM to compose <strong>3 grounded Arabic meal options</strong> with accurate macros.
          </p>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="btn btn-primary"
        style={{ width: '100%', marginTop: '8px', padding: '16px' }}
      >
        {isLoading ? (
          <>
            <Loader2 size={20} className="animate-pulse" style={{ animation: 'spin 1s linear infinite' }} />
            <span>Running LangGraph Pipeline (SSE Stream)...</span>
          </>
        ) : (
          <>
            <Play size={20} />
            <span>
              {generationMode === 'llm_arabic' && '🇪🇬 Generate Arabic Nutrition Plan'}
              {generationMode === 'llm_arabic_parquet' && '🗄️ Generate Parquet + Arabic Plan (3 Options)'}
              {generationMode === 'dataset' && 'Generate Clinical Nutrition Plan'}
            </span>
            <Sparkles size={18} />
          </>
        )}
      </button>
      <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
    </form>
  );
};
