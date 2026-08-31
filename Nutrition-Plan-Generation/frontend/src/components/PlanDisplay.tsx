import React, { useEffect, useState } from 'react';
import type { NutritionPlanResponse, MealPlan, Meal, TripleMealPlan, MealDistribution } from '../types';
import { Download, Sparkles, CheckCircle, AlertCircle, Utensils, Flame, Award, FileText, Code, Target } from 'lucide-react';
import confetti from 'canvas-confetti';
import { formatFoodDisplayName } from '../utils/foodDisplayFormatter';

interface PlanDisplayProps {
  planData: NutritionPlanResponse;
}

type OptionKey = 'option_a' | 'option_b' | 'option_c';
const OPTION_LABELS: { key: OptionKey; label: string; emoji: string; color: string }[] = [
  { key: 'option_a', label: 'Option A', emoji: '🅐', color: '#10b981' },
  { key: 'option_b', label: 'Option B', emoji: '🅑', color: '#06b6d4' },
  { key: 'option_c', label: 'Option C', emoji: '🅒', color: '#a78bfa' },
];

export const PlanDisplay: React.FC<PlanDisplayProps> = ({ planData }) => {
  const triplePlan: TripleMealPlan | undefined = planData.triple_meal_plan;
  const singlePlan: MealPlan | undefined = planData.meal_plan;
  const explanation = planData.explanation;
  const validation = planData.validation_report;
  const macros = planData.macro_result;
  const calories = planData.calories_result;
  const distribution: MealDistribution | undefined = triplePlan?.meal_distribution;

  // Active tab for triple plan
  const [activeOption, setActiveOption] = useState<OptionKey>('option_a');

  // Determine which meal plan to show
  const activeMealPlan: MealPlan | undefined = triplePlan
    ? triplePlan[activeOption]
    : singlePlan;

  const displayFoodName = (food: Meal['foods'][number]) =>
    formatFoodDisplayName(food, isArabicPlan);

  // Detect Arabic content
  const isArabicPlan = React.useMemo(() => {
    if (!activeMealPlan) return false;
    const arabicRegex = /[\u0600-\u06FF]/;
    const allFoods = [
      ...activeMealPlan.breakfast.foods,
      ...activeMealPlan.lunch.foods,
      ...activeMealPlan.dinner.foods,
      ...(activeMealPlan.snack?.foods ?? []),
    ];
    return allFoods.some(f => arabicRegex.test(f.name));
  }, [activeMealPlan]);

  // Detect whether this is the parquet-backed Arabic mode
  // (heuristic: triple plan + Arabic food names + distribution exists)
  const isParquetArabicPlan = React.useMemo(() => {
    return isArabicPlan && !!triplePlan && !!distribution;
  }, [isArabicPlan, triplePlan, distribution]);

  useEffect(() => {
    if (activeMealPlan) {
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#10b981', '#06b6d4', '#8b5cf6', '#f59e0b']
      });
    }
  }, []);  // fire once on mount

  if (!activeMealPlan) return null;

  // ── Markdown report generator ────────────────────────────────────────────────
  const generateMarkdownReport = (plan: MealPlan, optionLabel: string) => {
    let md = `# NutriGraph AI — Nutrition Plan Report (${optionLabel})\n`;
    md += `**Run ID:** ${planData.run_id}\n`;
    md += `**Goal:** ${calories?.goal || 'Specified Goal'} | **Activity Level:** ${calories?.activity_level || 'Moderate'}\n`;
    md += `**Target Daily Calories:** ${macros?.target_calories || plan.total_daily_calories} kcal\n\n`;
    md += `## Daily Targets vs Actuals\n`;
    md += `| Metric | Target | Actual | Status |\n`;
    md += `| :--- | :--- | :--- | :--- |\n`;
    md += `| **Calories** | ${macros?.target_calories || 'N/A'} kcal | ${plan.total_daily_calories.toFixed(0)} kcal | ${validation?.passed ? 'PASSED ±10%' : 'Check Warnings'} |\n`;
    md += `| **Protein** | ${macros?.protein_g || 'N/A'} g | ${plan.total_daily_protein_g.toFixed(1)} g | - |\n`;
    md += `| **Carbohydrates** | ${macros?.carbs_g || 'N/A'} g | ${plan.total_daily_carbs_g.toFixed(1)} g | - |\n`;
    md += `| **Healthy Fats** | ${macros?.fat_g || 'N/A'} g | ${plan.total_daily_fat_g.toFixed(1)} g | - |\n\n`;
    const meals: (Meal | undefined)[] = [plan.breakfast, plan.lunch, plan.dinner, plan.snack];
    md += `## Meal Composition\n\n`;
    meals.forEach(m => {
      if (m) {
        md += `### ${m.meal_name} (~${m.total_calories.toFixed(0)} kcal | P: ${m.total_protein_g.toFixed(1)}g, C: ${m.total_carbs_g.toFixed(1)}g, F: ${m.total_fat_g.toFixed(1)}g)\n`;
        md += `| Food Item | Serving (g) | Calories | Protein (g) | Carbs (g) | Fat (g) |\n`;
        md += `| :--- | :--- | :--- | :--- | :--- | :--- |\n`;
        m.foods.forEach(f => {
          md += `| ${displayFoodName(f)} | ${f.serving_grams.toFixed(0)}g | ${f.calories.toFixed(0)} kcal | ${f.protein_g.toFixed(1)}g | ${f.carbs_g.toFixed(1)}g | ${f.fat_g.toFixed(1)}g |\n`;
        });
        md += `\n`;
      }
    });
    if (explanation) {
      md += `## AI Clinical Rationale\n`;
      md += `**Summary:** ${explanation.summary}\n\n`;
      md += `**Calorie Rationale:** ${explanation.calorie_rationale}\n\n`;
      md += `**Macro Rationale:** ${explanation.macro_rationale}\n`;
    }
    return md;
  };

  const handleDownloadMarkdown = () => {
    const optLabel = triplePlan ? activeOption.replace('_', '-').toUpperCase() : 'Plan';
    const content = generateMarkdownReport(activeMealPlan, optLabel);
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `NutriGraph_${optLabel}_${planData.run_id.slice(0, 8)}.md`;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
  };

  const handleDownloadJSON = () => {
    const content = JSON.stringify(planData, null, 2);
    const blob = new Blob([content], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `NutriGraph_Plan_${planData.run_id.slice(0, 8)}.json`;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
  };

  // ── Render a single meal card ────────────────────────────────────────────────
  const renderMealCard = (meal: Meal | undefined, icon: string, slotKey?: string) => {
    if (!meal || meal.foods.length === 0) return null;
    const target = distribution && slotKey
      ? (distribution as any)[slotKey]
      : null;
    const devPct = target
      ? ((meal.total_calories - target.target_calories) / target.target_calories) * 100
      : null;

    return (
      <div className="meal-card fade-in">
        <div className="meal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.4rem' }}>{icon}</span>
            <div>
              <h4 style={{ fontSize: '1.1rem', color: '#f8fafc' }}>{meal.meal_name}</h4>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {meal.foods.length} items &bull; P: {meal.total_protein_g.toFixed(1)}g &bull; C: {meal.total_carbs_g.toFixed(1)}g &bull; F: {meal.total_fat_g.toFixed(1)}g
              </span>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
            <div className="badge badge-cyan" style={{ fontSize: '0.9rem', padding: '6px 12px' }}>
              {meal.total_calories.toFixed(0)} kcal
            </div>
            {target && (
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '3px' }}>
                <Target size={10} />
                <span>Target: {target.target_calories.toFixed(0)} kcal</span>
                {devPct !== null && (
                  <span style={{ color: Math.abs(devPct) <= 10 ? '#34d399' : '#fbbf24' }}>
                    &nbsp;({devPct > 0 ? '+' : ''}{devPct.toFixed(1)}%)
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        <table className="food-table">
          <thead>
            <tr>
              <th>Food Item</th>
              <th>Serving</th>
              <th>Calories</th>
              <th>Protein</th>
              <th>Carbs</th>
              <th>Fat</th>
            </tr>
          </thead>
          <tbody>
            {meal.foods.map((f, idx) => (
              <tr key={idx}>
                <td style={{
                  fontWeight: 500,
                  color: '#f8fafc',
                  direction: /[\u0600-\u06FF]/.test(displayFoodName(f)) ? 'rtl' : 'ltr',
                  fontFamily: /[\u0600-\u06FF]/.test(displayFoodName(f))
                    ? "'Cairo', 'Amiri', 'Noto Sans Arabic', sans-serif"
                    : 'inherit',
                  fontSize: /[\u0600-\u06FF]/.test(displayFoodName(f)) ? '0.95rem' : 'inherit',
                }}>{displayFoodName(f)}</td>
                <td>{f.serving_grams.toFixed(0)}g</td>
                <td>{f.calories.toFixed(0)} kcal</td>
                <td>{f.protein_g.toFixed(1)}g</td>
                <td>{f.carbs_g.toFixed(1)}g</td>
                <td>{f.fat_g.toFixed(1)}g</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // ── Render per-option daily summary row ──────────────────────────────────────
  const renderOptionSummaryRow = () => {
    if (!triplePlan) return null;
    return (
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '12px',
        marginBottom: '0',
      }}>
        {OPTION_LABELS.map(({ key, label, emoji, color }) => {
          const opt = triplePlan[key];
          const isActive = key === activeOption;
          return (
            <button
              key={key}
              onClick={() => setActiveOption(key)}
              style={{
                background: isActive
                  ? `linear-gradient(135deg, ${color}22, ${color}11)`
                  : 'rgba(255,255,255,0.03)',
                border: `2px solid ${isActive ? color : 'rgba(255,255,255,0.08)'}`,
                borderRadius: '14px',
                padding: '14px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                textAlign: 'center',
                color: '#f8fafc',
              }}
            >
              <div style={{ fontSize: '1.5rem', marginBottom: '4px' }}>{emoji}</div>
              <div style={{ fontWeight: 700, fontSize: '0.9rem', color: isActive ? color : '#f8fafc' }}>{label}</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: color, marginTop: '6px' }}>
                {opt.total_daily_calories.toFixed(0)}
                <span style={{ fontSize: '0.75rem', fontWeight: 400, color: 'var(--text-muted)' }}> kcal</span>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                P: {opt.total_daily_protein_g.toFixed(0)}g &bull; C: {opt.total_daily_carbs_g.toFixed(0)}g &bull; F: {opt.total_daily_fat_g.toFixed(0)}g
              </div>
            </button>
          );
        })}
      </div>
    );
  };

  // ── Main render ─────────────────────────────────────────────────────────────
  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

      {/* Header card */}
      <div className="glass-card" style={{
        padding: '20px 24px',
        background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(16, 185, 129, 0.15))',
        border: '1px solid rgba(139, 92, 246, 0.4)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '48px', height: '48px', borderRadius: '12px',
            background: 'rgba(139, 92, 246, 0.25)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#a78bfa'
          }}>
            <Award size={26} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.2rem' }}>
              {isParquetArabicPlan
                ? <>🗄️ خطتك الغذائية المصرية — أطعمة حقيقية!</>
                : isArabicPlan
                  ? <>🇪🇬 خطتك الغذائية المصرية جاهزة!</>
                  : <>Clinical Nutrition Plan Ready!</>}
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {triplePlan
                ? (isParquetArabicPlan
                  ? 'تم الاختيار من 793 طعام حقيقي وتوليد 3 خيارات — اختر الأنسب لك!'
                  : isArabicPlan
                    ? 'تم توليد 3 خيارات مختلفة — اختر الأنسب لك!'
                    : '3 independent options generated — pick your favourite!')
                : (isArabicPlan
                  ? 'وجبات مصرية أصيلة باللغة العربية.'
                  : 'All agents completed. Download your clinical report below.')
              }
            </p>
            {triplePlan && (
              <span style={{
                display: 'inline-flex', alignItems: 'center', gap: '4px', marginTop: '6px',
                padding: '3px 10px', borderRadius: '20px', fontSize: '0.72rem', fontWeight: 700,
                background: isParquetArabicPlan
                  ? 'rgba(245,158,11,0.15)'
                  : 'rgba(16,185,129,0.15)',
                color: isParquetArabicPlan ? '#fbbf24' : '#34d399',
                border: isParquetArabicPlan
                  ? '1px solid rgba(245,158,11,0.35)'
                  : '1px solid rgba(16,185,129,0.35)',
              }}>
                {isParquetArabicPlan
                  ? '🗄️ Parquet-Grounded Arabic — 3 Options'
                  : isArabicPlan
                    ? '🇪🇬 Free-form Arabic — 3 Options'
                    : '✨ Per-Slot Iterative Mode — 3 Options'}
              </span>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button onClick={handleDownloadMarkdown} className="btn btn-download">
            <FileText size={18} />
            <span>Download Report (.md)</span>
            <Download size={16} />
          </button>
          <button onClick={handleDownloadJSON} className="btn btn-secondary" style={{ padding: '10px 16px' }}>
            <Code size={18} />
            <span>Raw JSON</span>
          </button>
        </div>
      </div>

      {/* Daily macro summary (shows active option) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div className="glass-card" style={{ padding: '18px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
            <Flame size={14} color="#34d399" /> Daily Calories
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#34d399', marginTop: '6px' }}>
            {activeMealPlan.total_daily_calories.toFixed(0)} <span style={{ fontSize: '1rem', fontWeight: 400 }}>kcal</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Target: {macros?.target_calories != null ? macros.target_calories.toFixed(0) : 'N/A'} kcal
            {validation?.calorie_deviation_pct != null
              ? ` (${validation.calorie_deviation_pct > 0 ? '+' : ''}${validation.calorie_deviation_pct.toFixed(1)}% dev)`
              : ''}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '18px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>🍗 Protein</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#60a5fa', marginTop: '6px' }}>
            {activeMealPlan.total_daily_protein_g.toFixed(1)} <span style={{ fontSize: '1rem', fontWeight: 400 }}>g</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Target: {macros?.protein_g != null ? macros.protein_g.toFixed(1) : 'N/A'}g
          </div>
        </div>

        <div className="glass-card" style={{ padding: '18px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>🥔 Carbohydrates</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#fbbf24', marginTop: '6px' }}>
            {activeMealPlan.total_daily_carbs_g.toFixed(1)} <span style={{ fontSize: '1rem', fontWeight: 400 }}>g</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Target: {macros?.carbs_g != null ? macros.carbs_g.toFixed(1) : 'N/A'}g
          </div>
        </div>

        <div className="glass-card" style={{ padding: '18px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>🥑 Healthy Fats</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#f43f5e', marginTop: '6px' }}>
            {activeMealPlan.total_daily_fat_g.toFixed(1)} <span style={{ fontSize: '1rem', fontWeight: 400 }}>g</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Target: {macros?.fat_g != null ? macros.fat_g.toFixed(1) : 'N/A'}g
          </div>
        </div>
      </div>

      {/* Validation banner */}
      {validation && (
        <div className="glass-card" style={{
          padding: '14px 20px',
          background: validation.passed ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
          borderColor: validation.passed ? 'rgba(16, 185, 129, 0.4)' : 'rgba(245, 158, 11, 0.4)',
          display: 'flex', alignItems: 'center', gap: '12px'
        }}>
          {validation.passed
            ? <CheckCircle color="#34d399" size={22} />
            : <AlertCircle color="#fbbf24" size={22} />
          }
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, color: validation.passed ? '#34d399' : '#fbbf24' }}>
              Validation (Option A): {validation.passed ? 'PASSED ±10%' : 'Best-effort — minor deviations'}
            </div>
            {validation.issues && validation.issues.length > 0 && (
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                {validation.issues.map(i => `${i.rule}: ${i.actual}`).join(' | ')}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Option selector tabs (only for triple plan) */}
      {triplePlan && (
        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px', color: '#a78bfa' }}>
            <Sparkles size={18} /> Choose Your Meal Plan Option
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 400, marginLeft: '4px' }}>
              — 3 unique plans, same calorie targets
            </span>
          </h3>
          {renderOptionSummaryRow()}
        </div>
      )}

      {/* Meals for active option */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.3rem', marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Utensils className="gradient-text" size={20} />
          {triplePlan
            ? `${OPTION_LABELS.find(o => o.key === activeOption)?.label} — Daily Meal Breakdown`
            : 'Daily Meal Breakdown'
          }
        </h3>
        {renderMealCard(activeMealPlan.breakfast, '🍳', 'breakfast')}
        {renderMealCard(activeMealPlan.lunch, '🥗', 'lunch')}
        {renderMealCard(activeMealPlan.dinner, '🍲', 'dinner')}
        {renderMealCard(activeMealPlan.snack, '🍎', 'snack')}
      </div>

      {/* Explanation */}
      {explanation && (
        <div className="glass-card" style={{ padding: '24px', borderLeft: '4px solid #06b6d4' }}>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', color: '#22d3ee' }}>
            <Sparkles size={20} /> AI Clinical Rationale &amp; Doctor's Explanation
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.95rem', lineHeight: '1.6' }}>
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '14px', borderRadius: '10px' }}>
              <div style={{ fontWeight: 600, color: '#f8fafc', marginBottom: '4px' }}>📋 Clinical Summary:</div>
              <div style={{ color: 'var(--text-muted)' }}>{explanation.summary}</div>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '14px', borderRadius: '10px' }}>
              <div style={{ fontWeight: 600, color: '#f8fafc', marginBottom: '4px' }}>🔥 Calorie Adjustment Rationale:</div>
              <div style={{ color: 'var(--text-muted)' }}>{explanation.calorie_rationale}</div>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '14px', borderRadius: '10px' }}>
              <div style={{ fontWeight: 600, color: '#f8fafc', marginBottom: '4px' }}>⚖️ Macronutrient Split Rationale:</div>
              <div style={{ color: 'var(--text-muted)' }}>{explanation.macro_rationale}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
