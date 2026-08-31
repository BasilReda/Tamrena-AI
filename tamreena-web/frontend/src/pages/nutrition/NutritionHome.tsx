import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { getLastNutritionRunId } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';

/**
 * Entry point for the "Nutrition" nav link. Resumes the user's most recent
 * plan (if any) instead of always dropping them on a blank intake form —
 * the run_id otherwise only ever lived in the results page's URL.
 */
function NutritionHome() {
  const { t } = useTranslation();
  const [runId, setRunId] = useState<string | null | undefined>(undefined);

  useEffect(() => {
    getLastNutritionRunId()
      .then(setRunId)
      .catch(() => setRunId(null));
  }, []);

  if (runId === undefined) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
        <p style={{ fontWeight: 600 }}>{t('nutrition.home.loading')}</p>
      </div>
    );
  }

  return <Navigate to={runId ? `/nutrition/results/${encodeURIComponent(runId)}` : '/nutrition/intake'} replace />;
}

export default NutritionHome;
