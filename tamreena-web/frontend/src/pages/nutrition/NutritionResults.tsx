import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getNutritionResult, type NutritionResult, type NutritionMeal, type NutritionMealPlan } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';

/** Arabic text uses Unicode range U+0600–U+06FF; detect it to switch to RTL layout. */
const isArabicText = (text: string): boolean => /[؀-ۿ]/.test(text);

function MealCard({ meal, index, rtl }: { meal: NutritionMeal; index: number; rtl: boolean }) {
  const { t } = useTranslation();
  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '20px' }} dir={rtl ? 'rtl' : 'ltr'}>
      {/* Meal Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', borderBottom: '1px solid var(--border)', paddingBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ background: 'rgba(6, 182, 212, 0.15)', color: 'var(--category-data)', border: '1px solid rgba(6, 182, 212, 0.3)', width: '32px', height: '32px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '14px' }}>
            {index}
          </span>
          <h3 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-heading)', margin: 0 }}>
            {meal.meal_name}
          </h3>
        </div>
        <span className="badge badge-cyan">
          {t('nutrition.results.balancedMacros')}
        </span>
      </div>

      {/* Foods List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '18px' }}>
        {meal.foods.map((food, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', background: 'var(--bg-input)', borderRadius: '12px', border: '1px solid var(--border)' }}>
            <div>
              <span style={{ fontSize: '14.5px', fontWeight: 600, color: 'var(--text-heading)' }}>{food.name}</span>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)', margin: rtl ? '0 8px 0 0' : '0 0 0 8px' }}>({food.serving_grams}g serving)</span>
            </div>
            <div style={{ display: 'flex', gap: '16px', fontSize: '14px', color: 'var(--text-body)', fontFamily: 'var(--font-mono)' }}>
              <span>{food.calories} <small style={{ color: 'var(--text-muted)' }}>kcal</small></span>
              <span style={{ fontWeight: 700, color: 'var(--category-nutrition)' }}>{food.protein_g}g <small style={{ color: 'var(--text-muted)', fontWeight: 400 }}>P</small></span>
            </div>
          </div>
        ))}
      </div>

      {/* Meal Macro Summary Footer */}
      <div style={{ background: 'var(--bg-input)', borderRadius: '12px', padding: '12px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '13px', fontWeight: 700, color: 'var(--text-body)' }}>
        <span>{t('nutrition.results.mealTotal')}</span>
        <div style={{ display: 'flex', gap: '12px', color: 'var(--text-heading)', fontFamily: 'var(--font-mono)' }}>
          <span style={{ color: 'var(--category-ai)' }}>{meal.total_calories} kcal</span>
          <span>·</span>
          <span style={{ color: 'var(--category-nutrition)' }}>{meal.total_protein_g}g Protein</span>
          <span>·</span>
          <span style={{ color: 'var(--category-data)' }}>{meal.total_carbs_g}g Carbs</span>
          <span>·</span>
          <span style={{ color: 'var(--category-motion)' }}>{meal.total_fat_g}g Fat</span>
        </div>
      </div>
    </div>
  );
}

function DayPlan({ plan, rtl }: { plan: NutritionMealPlan; rtl: boolean }) {
  return (
    <div>
      <MealCard meal={plan.breakfast} index={1} rtl={rtl} />
      <MealCard meal={plan.lunch} index={2} rtl={rtl} />
      <MealCard meal={plan.dinner} index={3} rtl={rtl} />
      {plan.snack && <MealCard meal={plan.snack} index={4} rtl={rtl} />}
      {plan.notes && (
        <p dir={rtl ? 'rtl' : 'ltr'} style={{ color: 'var(--text-body)', fontSize: '13.5px', marginTop: '4px' }}>
          {plan.notes}
        </p>
      )}
    </div>
  );
}

const PLAN_OPTION_LABELS = { option_a: 'Option A', option_b: 'Option B', option_c: 'Option C' } as const;

function NutritionResults() {
  const { t } = useTranslation();
  const { runId } = useParams<{ runId: string }>();
  const [result, setResult] = useState<NutritionResult | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [activeOption, setActiveOption] = useState<keyof typeof PLAN_OPTION_LABELS>('option_a');

  useEffect(() => {
    if (!runId) return;
    getNutritionResult(runId)
      .then(setResult)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load nutrition result'));
  }, [runId]);

  if (error) {
    return <div style={{ padding: '20px', borderRadius: '12px', background: 'color-mix(in srgb, var(--status-error) 15%, transparent)', color: 'var(--status-error)' }}>⚠️ {error}</div>;
  }

  if (result === undefined) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-body)' }}>
        <p style={{ fontWeight: 600 }}>{t('nutrition.results.loading')}</p>
      </div>
    );
  }

  if (result === null) {
    return (
      <div className="glass-panel" style={{ padding: '48px', textAlign: 'center', maxWidth: '500px', margin: '40px auto' }}>
        <p style={{ color: 'var(--text-body)', marginBottom: '20px' }}>{t('nutrition.results.stillGenerating')}</p>
        <Link to="/nutrition/intake" className="btn btn-primary">
          {t('nutrition.results.backToIntake')}
        </Link>
      </div>
    );
  }

  const { macro_result, meal_plan, triple_meal_plan, explanation } = result;
  const rtl = isArabicText(
    triple_meal_plan?.option_a.breakfast.meal_name ?? meal_plan?.breakfast.meal_name ?? ''
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Top Header & Actions */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <span className="badge badge-cyan">
              {triple_meal_plan ? t('nutrition.results.badgeArabic') : t('nutrition.results.badgeDataset')}
            </span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{t('nutrition.results.generatedToday')}</span>
          </div>
          <h1 style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text-heading)', margin: 0, letterSpacing: '-0.02em' }}>
            {t('nutrition.results.title')}
          </h1>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <Link to="/nutrition/intake" className="btn btn-secondary">
            {t('nutrition.results.generateNew')}
          </Link>
          <button onClick={() => window.print()} className="btn btn-secondary">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"></path></svg>
            {t('nutrition.results.exportPdf')}
          </button>
        </div>
      </div>

      {/* Macro Summary Card */}
      {macro_result && (
        <div id="nutrition-macro-summary" className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <span style={{ color: 'var(--category-data)' }}>⚡</span>
            <h2 style={{ fontSize: '11px', fontWeight: 800, letterSpacing: '0.08em', color: 'var(--text-body)', textTransform: 'uppercase', margin: 0 }}>
              {t('nutrition.results.macroSummary')}
            </h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '14px' }}>
            <div className="glass-panel" style={{ padding: '16px', textAlign: 'center', background: 'var(--bg-input)' }}>
              <span className="metric-val" style={{ fontSize: '28px', color: 'var(--category-ai)', display: 'block' }}>
                {macro_result.target_calories}
              </span>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>{t('nutrition.results.targetKcal')}</span>
            </div>
            <div className="glass-panel" style={{ padding: '16px', textAlign: 'center', background: 'var(--bg-input)' }}>
              <span className="metric-val" style={{ fontSize: '28px', color: 'var(--category-nutrition)', display: 'block' }}>
                {macro_result.protein_g}g
              </span>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>{t('nutrition.results.protein')}</span>
            </div>
            <div className="glass-panel" style={{ padding: '16px', textAlign: 'center', background: 'var(--bg-input)' }}>
              <span className="metric-val" style={{ fontSize: '28px', color: 'var(--category-data)', display: 'block' }}>
                {macro_result.carbs_g}g
              </span>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>{t('nutrition.results.carbs')}</span>
            </div>
            <div className="glass-panel" style={{ padding: '16px', textAlign: 'center', background: 'var(--bg-input)' }}>
              <span className="metric-val" style={{ fontSize: '28px', color: 'var(--category-motion)', display: 'block' }}>
                {macro_result.fat_g}g
              </span>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>{t('nutrition.results.fat')}</span>
            </div>
          </div>
        </div>
      )}

      {/* Meal Plan Schedule (dataset mode: single English plan) */}
      {meal_plan && !triple_meal_plan && (
        <div id="nutrition-meal-plan">
          <h2 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '16px' }}>
            {t('nutrition.results.mealSchedule')}
          </h2>
          <DayPlan plan={meal_plan} rtl={false} />
        </div>
      )}

      {/* Triple Meal Plan (llm_arabic mode: 3 full-day Arabic options) */}
      {triple_meal_plan && (
        <div id="nutrition-meal-plan">
          <h2 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-heading)', marginBottom: '16px' }} dir={rtl ? 'rtl' : 'ltr'}>
            {rtl ? t('nutrition.results.mealScheduleAr') : t('nutrition.results.mealSchedule')}
          </h2>

          <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
            {(Object.keys(PLAN_OPTION_LABELS) as Array<keyof typeof PLAN_OPTION_LABELS>).map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => setActiveOption(key)}
                className={activeOption === key ? 'btn btn-cyan' : 'btn btn-secondary'}
                style={{ padding: '10px 20px', fontSize: '14px' }}
              >
                {PLAN_OPTION_LABELS[key]}
              </button>
            ))}
          </div>

          <DayPlan plan={triple_meal_plan[activeOption]} rtl={rtl} />

          {triple_meal_plan.notes && (
            <p dir={rtl ? 'rtl' : 'ltr'} style={{ color: 'var(--text-body)', fontSize: '13.5px' }}>
              {triple_meal_plan.notes}
            </p>
          )}
        </div>
      )}

      {/* AI Explanation Accordion Box */}
      {explanation && (
        <div
          style={{
            background: 'rgba(6, 182, 212, 0.1)',
            border: '1px solid rgba(6, 182, 212, 0.3)',
            borderRadius: '16px',
            padding: '24px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <span style={{ color: 'var(--category-data)', fontSize: '18px' }}>💡</span>
            <h3 style={{ fontSize: '12px', fontWeight: 800, letterSpacing: '0.08em', color: 'var(--category-data)', textTransform: 'uppercase', margin: 0 }}>
              {t('nutrition.results.aiRationale')}
            </h3>
          </div>
          <p style={{ fontSize: '14.5px', color: 'var(--text-body)', lineHeight: 1.6, marginBottom: '16px' }}>
            {explanation.summary}
          </p>
          {explanation.adherence_tips.length > 0 && (
            <div>
              <span style={{ fontSize: '12px', fontWeight: 800, color: 'var(--text-body)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: '8px' }}>
                {t('nutrition.results.adherenceTips')}
              </span>
              <ul style={{ margin: 0, paddingLeft: '20px', color: 'var(--text-body)', fontSize: '13.5px', lineHeight: 1.6 }}>
                {explanation.adherence_tips.map((tip, i) => (
                  <li key={i} style={{ marginBottom: '4px' }}>{tip}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default NutritionResults;
