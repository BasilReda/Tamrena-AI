import { BrowserRouter, Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './lib/auth-context';
import { PreferencesProvider } from './lib/preferences-context';
import AuthScreen from './pages/AuthScreen';
import ProtectedLayout from './components/shell/ProtectedLayout';
import PublicLayout from './components/public/PublicLayout';
import LandingHome from './pages/public/LandingHome';
import AboutPage from './pages/public/AboutPage';

import PricingPage from './pages/public/PricingPage';
import Home from './pages/Home';
import WorkoutTab from './pages/workout/WorkoutTab';
import PlanView from './pages/workout/PlanView';
import IntakeFlow from './pages/intake/IntakeFlow';
import CaptureScreen from './pages/CaptureScreen';
import ProcessingScreen from './pages/ProcessingScreen';
import ProgressTab from './pages/progress/ProgressTab';
import ExercisesHub from './pages/exercises/ExercisesHub';
import ExerciseDetail from './pages/exercises/ExerciseDetail';
import NutritionHome from './pages/nutrition/NutritionHome';
import NutritionIntake from './pages/nutrition/NutritionIntake';
import NutritionGenerating from './pages/nutrition/NutritionGenerating';
import NutritionResults from './pages/nutrition/NutritionResults';
import LiveSession from './pages/live-session/LiveSession';
import CoachChat from './pages/coach/CoachChat';
import { getToken } from './lib/api';

function SignInRoute() {
  const navigate = useNavigate();
  const { refresh } = useAuth();

  if (getToken()) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <AuthScreen
      onSignedIn={async () => {
        await refresh();
        navigate('/dashboard');
      }}
    />
  );
}

function App() {
  return (
    <BrowserRouter>
      <PreferencesProvider>
      <AuthProvider>
        <Routes>
          {/* Public Marketing & PRD Pages */}
          <Route element={<PublicLayout />}>
            <Route path="/" element={<LandingHome />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/technology" element={<Navigate to="/" replace />} />
            <Route path="/project-info" element={<Navigate to="/" replace />} />
            <Route path="/pricing" element={<PricingPage />} />
          </Route>

          {/* Authentication */}
          <Route path="/signin" element={<SignInRoute />} />

          {/* Authenticated Athlete Command Center */}
          <Route element={<ProtectedLayout />}>
            <Route path="/dashboard" element={<Home />} />
            <Route path="/workout" element={<WorkoutTab />} />
            <Route path="/workout/:sessionId" element={<PlanView />} />
            <Route path="/progress" element={<ProgressTab />} />
            <Route path="/exercises" element={<ExercisesHub />} />
            <Route path="/exercises/detail" element={<ExerciseDetail />} />
            <Route path="/coach" element={<CoachChat />} />
            <Route path="/nutrition" element={<NutritionHome />} />
            <Route path="/nutrition/intake" element={<NutritionIntake />} />
            <Route path="/nutrition/generating" element={<NutritionGenerating />} />
            <Route path="/nutrition/results/:runId" element={<NutritionResults />} />
          </Route>

          {/* Standalone Flows */}
          <Route path="/intake" element={<IntakeFlow />} />
          <Route path="/capture" element={<CaptureScreen />} />
          <Route path="/processing" element={<ProcessingScreen />} />
          <Route path="/exercises/live-session" element={<LiveSession />} />

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
      </PreferencesProvider>
    </BrowserRouter>
  );
}

export default App;
