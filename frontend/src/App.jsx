import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import BackgroundCanvas from './components/motion/BackgroundCanvas';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Challenges from './pages/Challenges';
import ChallengeDetails from './pages/ChallengeDetails';
import Workspace from './pages/Workspace';
import SubmissionHistory from './pages/SubmissionHistory';
import Leaderboard from './pages/Leaderboard';
import PublicProfile from './pages/PublicProfile';
import RecruiterDashboard from './pages/RecruiterDashboard';

export default function App() {
  return (
    <AuthProvider>
      <div className="app-container">
        <BackgroundCanvas />
        <Navbar />
        <div className="main-content">
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/profile/:username" element={<PublicProfile />} />

            {/* Protected Routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/challenges"
              element={
                <ProtectedRoute>
                  <Challenges />
                </ProtectedRoute>
              }
            />
            <Route
              path="/leaderboard"
              element={
                <ProtectedRoute>
                  <Leaderboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/recruiter"
              element={
                <ProtectedRoute>
                  <RecruiterDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/recruiter/compare"
              element={
                <ProtectedRoute>
                  <RecruiterDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/challenges/:id"
              element={
                <ProtectedRoute>
                  <ChallengeDetails />
                </ProtectedRoute>
              }
            />
            <Route
              path="/workspace/:id"
              element={
                <ProtectedRoute>
                  <Workspace />
                </ProtectedRoute>
              }
            />
            <Route
              path="/submissions"
              element={
                <ProtectedRoute>
                  <SubmissionHistory />
                </ProtectedRoute>
              }
            />
          </Routes>
        </div>
      </div>
    </AuthProvider>
  );
}
