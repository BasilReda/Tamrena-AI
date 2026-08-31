import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { generateNutritionPlan, type NutritionIntakeAnswers } from '../../lib/api';
import { FormStepWizard } from '../../components/ui/FormStepWizard';
import { PillGroup, type Option } from '../../components/ui/PillGroup';
import { useTranslation } from '../../lib/i18n';

const AGE_DROPDOWN_OPTIONS = Array.from({ length: 70 }, (_, i) => 16 + i);
const HEIGHT_DROPDOWN_OPTIONS = Array.from({ length: 81 }, (_, i) => 140 + i);
const WEIGHT_DROPDOWN_OPTIONS = Array.from({ length: 141 }, (_, i) => 40 + i);

const PREFERRED_FOODS_DROPDOWN_OPTIONS = [
  { value: 'Chicken breast, Jasmine rice, Eggs, Oats', label: 'Classic Bodybuilder (Chicken, Rice, Eggs, Oats)' },
  { value: 'Salmon, Sweet potato, Eggs, Avocado, Spinach', label: 'Healthy Fats & Seafood (Salmon, Sweet Potato, Avocado)' },
  { value: 'Lean beef, White rice, Eggs, Broccoli, Almonds', label: 'Red Meat Power (Beef, Rice, Eggs, Broccoli)' },
  { value: 'Tofu, Quinoa, Lentils, Avocado, Olive oil', label: 'Plant Based (Tofu, Quinoa, Lentils, Avocado)' },
  { value: 'Turkey breast, Rice cakes, Whey protein, Asparagus', label: 'Shredding Prep (Turkey, Rice Cakes, Whey, Asparagus)' },
  { value: 'Eggs, Beef, Avocado, Cheese, Butter', label: 'Keto Clean (Eggs, Beef, Avocado, Cheese)' },
];

const ALLERGIES_DROPDOWN_OPTIONS = [
  { value: '', label: 'None (No Known Allergies)' },
  { value: 'Dairy, Lactose', label: 'Dairy & Lactose Intolerance' },
  { value: 'Peanuts, Tree nuts', label: 'Peanuts & Tree Nuts' },
  { value: 'Gluten, Wheat', label: 'Gluten & Wheat Sensitivity' },
  { value: 'Shellfish, Fish', label: 'Shellfish & Fish' },
  { value: 'Soy', label: 'Soy' },
  { value: 'Eggs', label: 'Eggs' },
];

function NutritionIntake() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);

  // Form State
  const [age, setAge] = useState(28);
  const [gender, setGender] = useState<NutritionIntakeAnswers['gender']>('male');
  const [heightCm, setHeightCm] = useState(178);
  const [weightKg, setWeightKg] = useState(78);
  const [goal, setGoal] = useState<NutritionIntakeAnswers['goal']>('muscle_gain');
  const [activityLevel, setActivityLevel] = useState<NutritionIntakeAnswers['activity_level']>('moderate');
  const [dietType, setDietType] = useState<NutritionIntakeAnswers['diet_type']>('high_protein');
  const [preferences, setPreferences] = useState('Chicken breast, Jasmine rice, Eggs, Oats');
  const [allergies, setAllergies] = useState('');
  const [additionalNotes, setAdditionalNotes] = useState('');
  const [mealGenerationMode, setMealGenerationMode] = useState<'dataset' | 'llm_arabic'>('dataset');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const GENDER_OPTIONS: Option<NutritionIntakeAnswers['gender']>[] = [
    { value: 'male', label: 'Male' },
    { value: 'female', label: 'Female' },
  ];

  const GOAL_OPTIONS: Option<NutritionIntakeAnswers['goal']>[] = [
    { value: 'fat_loss', label: 'Fat Loss', sublabel: 'Trim body fat' },
    { value: 'weight_loss', label: 'Weight Loss', sublabel: 'Deficit' },
    { value: 'muscle_gain', label: 'Muscle Gain', sublabel: 'Hypertrophy' },
    { value: 'bulking', label: 'Bulking', sublabel: 'Surplus' },
    { value: 'maintenance', label: 'Maintenance', sublabel: 'Equilibrium' },
    { value: 'recomposition', label: 'Recomposition', sublabel: 'Fat loss + Muscle' },
  ];

  const ACTIVITY_OPTIONS: Option<NutritionIntakeAnswers['activity_level']>[] = [
    { value: 'sedentary', label: 'Sedentary' },
    { value: 'lightly_active', label: 'Lightly Active' },
    { value: 'moderate', label: 'Moderate' },
    { value: 'very_active', label: 'Very Active' },
    { value: 'extra_active', label: 'Extra Active' },
  ];

  const DIET_OPTIONS: Option<NutritionIntakeAnswers['diet_type']>[] = [
    { value: 'normal', label: 'Standard Balanced' },
    { value: 'high_protein', label: 'High Protein' },
    { value: 'vegetarian', label: 'Vegetarian' },
    { value: 'vegan', label: 'Vegan' },
    { value: 'keto', label: 'Keto' },
  ];

  const LANGUAGE_OPTIONS: Option<'dataset' | 'llm_arabic'>[] = [
    { value: 'dataset', label: 'English', sublabel: 'Egyptian food dataset' },
    { value: 'llm_arabic', label: 'Arabic', sublabel: 'اللغة العربية · 3 plan options' },
  ];

  const parseList = (value: string): string[] =>
    value.split(',').map((item) => item.trim()).filter(Boolean);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const { run_id } = await generateNutritionPlan({
        age,
        gender,
        height_cm: heightCm,
        weight_kg: weightKg,
        goal,
        activity_level: activityLevel,
        diet_type: dietType,
        preferences: parseList(preferences),
        allergies: parseList(allergies),
        additional_notes: additionalNotes || undefined,
        meal_generation_mode: mealGenerationMode,
      });
      navigate('/nutrition/generating', { state: { run_id } });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start nutrition plan generation');
      setSubmitting(false);
    }
  };

  const steps = [
    { title: t('nutrition.intake.steps.biometrics') },
    { title: t('nutrition.intake.steps.goals') },
    { title: t('nutrition.intake.steps.preferences') },
  ];

  return (
    <div style={{ maxWidth: '760px', margin: '0 auto', padding: 'clamp(16px, 3vw, 32px) clamp(12px, 3vw, 24px)' }}>
      <div style={{ marginBottom: '24px' }}>
        <span className="badge badge-cyan" style={{ marginBottom: '10px' }}>{t('nutrition.intake.badge')}</span>
        <h1 style={{ fontSize: 'clamp(22px, 4vw, 32px)', fontWeight: 800, color: '#ffffff', margin: '0 0 8px 0', letterSpacing: '-0.02em' }}>
          {t('nutrition.intake.title')}
        </h1>
        <p style={{ color: '#cbd5e1', fontSize: '14px', margin: 0 }}>
          {t('nutrition.intake.subtitle')}
        </p>
      </div>

      <div className="glass-panel glow-card-cyan" style={{ padding: 'clamp(18px, 4vw, 36px)', background: 'rgba(10, 20, 56, 0.9)' }}>
        <FormStepWizard steps={steps} currentStep={step} onStepClick={(s) => setStep(s)} />

        <form onSubmit={handleSubmit}>
          {/* STEP 1: BIOMETRICS */}
          {step === 1 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '20px' }}>
              <div style={{ borderBottom: '1px solid rgba(112, 128, 144, 0.25)', paddingBottom: '10px' }}>
                <h3 style={{ fontSize: '17px', fontWeight: 800, color: '#ffffff', margin: 0 }}>
                  {t('nutrition.intake.step1.title')}
                </h3>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">{t('nutrition.intake.age')}</label>
                  <select
                    id="nutrition-age"
                    value={age}
                    onChange={(e) => setAge(Number(e.target.value))}
                    className="form-input"
                    required
                  >
                    {AGE_DROPDOWN_OPTIONS.map((a) => (
                      <option key={a} value={a} style={{ background: '#050c24' }}>
                        {a} Years Old
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label" style={{ marginBottom: '8px' }}>{t('nutrition.intake.gender')}</label>
                  <PillGroup options={GENDER_OPTIONS} value={gender} onChange={setGender} idPrefix="nutrition-gender" />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">{t('nutrition.intake.height')}</label>
                  <select
                    id="nutrition-height"
                    value={heightCm}
                    onChange={(e) => setHeightCm(Number(e.target.value))}
                    className="form-input"
                    required
                  >
                    {HEIGHT_DROPDOWN_OPTIONS.map((h) => (
                      <option key={h} value={h} style={{ background: '#050c24' }}>
                        {h} cm
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">{t('nutrition.intake.weight')}</label>
                  <select
                    id="nutrition-weight"
                    value={weightKg}
                    onChange={(e) => setWeightKg(Number(e.target.value))}
                    className="form-input"
                    required
                  >
                    {WEIGHT_DROPDOWN_OPTIONS.map((w) => (
                      <option key={w} value={w} style={{ background: '#050c24' }}>
                        {w} kg
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '12px' }}>
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="btn btn-primary"
                  style={{ padding: '12px 28px', fontSize: '14px' }}
                >
                  <span>{t('nutrition.intake.next1')}</span>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"></path></svg>
                </button>
              </div>
            </div>
          )}

          {/* STEP 2: GOALS & ACTIVITY */}
          {step === 2 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '20px' }}>
              <div style={{ borderBottom: '1px solid rgba(112, 128, 144, 0.25)', paddingBottom: '10px' }}>
                <h3 style={{ fontSize: '17px', fontWeight: 800, color: '#ffffff', margin: 0 }}>
                  {t('nutrition.intake.step2.title')}
                </h3>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ marginBottom: '8px' }}>{t('nutrition.intake.goal')}</label>
                <PillGroup options={GOAL_OPTIONS} value={goal} onChange={setGoal} idPrefix="nutrition-goal" />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ marginBottom: '8px' }}>{t('nutrition.intake.activity')}</label>
                <PillGroup options={ACTIVITY_OPTIONS} value={activityLevel} onChange={setActivityLevel} idPrefix="nutrition-activity" />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ marginBottom: '8px' }}>{t('nutrition.intake.diet')}</label>
                <PillGroup options={DIET_OPTIONS} value={dietType} onChange={setDietType} idPrefix="nutrition-diet" />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', flexWrap: 'wrap', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="btn btn-secondary"
                >
                  {t('nutrition.intake.back')}
                </button>
                <button
                  type="button"
                  onClick={() => setStep(3)}
                  className="btn btn-primary"
                  style={{ padding: '12px 28px', fontSize: '14px' }}
                >
                  <span>{t('nutrition.intake.next2')}</span>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"></path></svg>
                </button>
              </div>
            </div>
          )}

          {/* STEP 3: PREFERENCES & NOTES */}
          {step === 3 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '20px' }}>
              <div style={{ borderBottom: '1px solid rgba(112, 128, 144, 0.25)', paddingBottom: '10px' }}>
                <h3 style={{ fontSize: '17px', fontWeight: 800, color: '#ffffff', margin: 0 }}>
                  {t('nutrition.intake.step3.title')}
                </h3>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label" style={{ marginBottom: '8px' }}>{t('nutrition.intake.planLanguage')}</label>
                <PillGroup options={LANGUAGE_OPTIONS} value={mealGenerationMode} onChange={setMealGenerationMode} idPrefix="nutrition-language" />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">{t('nutrition.intake.foodProfile')}</label>
                <select
                  id="nutrition-preferences"
                  value={preferences}
                  onChange={(e) => setPreferences(e.target.value)}
                  className="form-input"
                >
                  {PREFERRED_FOODS_DROPDOWN_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value} style={{ background: '#050c24' }}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">{t('nutrition.intake.allergies')}</label>
                <select
                  id="nutrition-allergies"
                  value={allergies}
                  onChange={(e) => setAllergies(e.target.value)}
                  className="form-input"
                >
                  {ALLERGIES_DROPDOWN_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value} style={{ background: '#050c24' }}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">{t('nutrition.intake.notes')}</label>
                <textarea
                  id="nutrition-additional-notes"
                  value={additionalNotes}
                  onChange={(e) => setAdditionalNotes(e.target.value)}
                  placeholder={t('nutrition.intake.notesPh')}
                  maxLength={500}
                  rows={3}
                  className="form-input"
                  style={{ height: '80px', resize: 'vertical' }}
                />
              </div>

              {error && (
                <div style={{ padding: '12px', borderRadius: '10px', background: 'rgba(255, 23, 68, 0.12)', border: '1px solid rgba(255, 23, 68, 0.3)', color: '#ff80ab', fontSize: '13px' }}>
                  ⚠️ {error}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', flexWrap: 'wrap', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="btn btn-secondary"
                >
                  {t('nutrition.intake.back')}
                </button>
                <button
                  id="nutrition-intake-submit"
                  type="submit"
                  disabled={submitting}
                  className="btn btn-primary"
                  style={{ padding: '12px 28px', fontSize: '14px' }}
                >
                  <span>{submitting ? t('nutrition.intake.submitting') : t('nutrition.intake.submit')}</span>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"></path></svg>
                </button>
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

export default NutritionIntake;
