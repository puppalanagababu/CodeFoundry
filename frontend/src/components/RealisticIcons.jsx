import React from 'react';
import {
  Bug,
  ShieldCheck,
  ShieldAlert,
  Zap,
  Activity,
  Layers,
  FlaskConical,
  Database,
  Globe,
  Terminal,
  FileCode2,
  FileText,
  File,
  Folder,
  FolderOpen,
  Lock,
  Unlock,
  Search,
  SearchX,
  Trophy,
  Medal,
  Award,
  Crown,
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  ExternalLink,
  Eye,
  Users,
  UserX,
  BarChart3,
  Cpu,
  Server,
  Code2,
  GitCommit,
  GitPullRequest,
  Inbox,
  Sparkles,
  RotateCcw,
  Play,
  X,
} from 'lucide-react';

/**
 * Returns a realistic SVG icon for challenge categories / engineering incidents.
 */
export function getIncidentIcon(type, size = 18, color) {
  const norm = (type || '').toUpperCase();
  switch (norm) {
    case 'BUG_FIX':
    case 'DEBUGGING':
      return <Bug size={size} color={color || '#DC2626'} />;
    case 'API':
      return <Globe size={size} color={color || '#1D4ED8'} />;
    case 'SECURITY':
      return <ShieldAlert size={size} color={color || '#6D28D9'} />;
    case 'PERFORMANCE':
      return <Activity size={size} color={color || '#047857'} />;
    case 'DATABASE':
      return <Database size={size} color={color || '#9A3412'} />;
    case 'TESTING':
      return <FlaskConical size={size} color={color || '#0E7490'} />;
    case 'CODE_REVIEW':
    case 'REFACTORING':
      return <GitPullRequest size={size} color={color || '#6D45C5'} />;
    default:
      return <Layers size={size} color={color || '#6D45C5'} />;
  }
}

/**
 * Returns a realistic SVG icon for the 6 core engineering competencies.
 */
export function getSkillIcon(skillKey, size = 18, color) {
  const norm = (skillKey || '').toLowerCase();
  switch (norm) {
    case 'problem_solving':
      return <Zap size={size} color={color || '#1D4ED8'} />;
    case 'debugging':
      return <Bug size={size} color={color || '#DC2626'} />;
    case 'security':
      return <ShieldCheck size={size} color={color || '#6D28D9'} />;
    case 'performance':
      return <Activity size={size} color={color || '#047857'} />;
    case 'code_quality':
      return <Layers size={size} color={color || '#D97706'} />;
    case 'testing':
      return <FlaskConical size={size} color={color || '#0E7490'} />;
    default:
      return <Code2 size={size} color={color || '#6D45C5'} />;
  }
}

/**
 * Realistic Brand / Tech Stack SVGs
 */
export function TechLogo({ name, size = 20, className = '' }) {
  const norm = (name || '').toLowerCase();

  switch (norm) {
    case 'python':
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
          <path d="M11.91 2c-5.26 0-4.93 2.28-4.93 2.28l.01 2.37h5.03v.71H4.95S2 7.04 2 12.35c0 5.3 2.58 5.14 2.58 5.14h1.54v-2.17s-.08-2.58 2.54-2.58h4.35s2.44.04 2.44-2.39V4.67S15.89 2 11.91 2zm-1.42 1.45c.48 0 .87.39.87.87s-.39.87-.87.87-.87-.39-.87-.87.39-.87.87-.87z" fill="#3776AB"/>
          <path d="M12.09 22c5.26 0 4.93-2.28 4.93-2.28l-.01-2.37h-5.03v-.71h7.06S22 16.96 22 11.65c0-5.3-2.58-5.14-2.58-5.14h-1.54v2.17s.08 2.58-2.54 2.58h-4.35s-2.44-.04-2.44 2.39v7.68s-.44 2.67 3.54 2.67zm1.42-1.45c-.48 0-.87-.39-.87-.87s.39-.87.87-.87.87.39.87.87-.39.87-.87.87z" fill="#FFD43B"/>
        </svg>
      );
    case 'docker':
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
          <path d="M13.98 10.9h2.08v1.98h-2.08V10.9zm-2.6 0h2.08v1.98h-2.08V10.9zm-2.6 0h2.08v1.98H8.78V10.9zm-2.6 0h2.08v1.98H6.18V10.9zm7.8-2.49h2.08v1.98h-2.08V8.41zm-2.6 0h2.08v1.98h-2.08V8.41zm-2.6 0h2.08v1.98H8.78V8.41zm5.2-2.5h2.08v1.98h-2.08V5.91zm7.4 6.9c-.38-.28-1.4-.41-2.28-.32-.14-.73-.55-1.4-1.22-1.92l-.53-.41-.36.56c-.39.6-.5 1.45-.33 2.13-.3.17-.67.31-1.09.43l-.35.1-9.52.01c-.48 0-.93-.05-1.37-.16-.62-.16-1.59-.65-1.99-1.56-.25-.56-.27-1.36-.08-2.07l.06-.24-.25.04c-.7.1-1.37.45-1.87.97-.68.71-1.03 1.68-1 2.7.07 2.17 1.5 3.93 3.63 4.47 1.15.29 8.1.33 9.47.16 2.37-.29 4.38-1.51 5.48-3.32.74-.08 1.48-.34 2.11-.79.37-.26.83-.69.83-.69l-.33-.51z" fill="#2496ED"/>
        </svg>
      );
    case 'react':
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
          <ellipse cx="12" cy="12" rx="4" ry="10" transform="rotate(30 12 12)" stroke="#61DAFB" strokeWidth="1.5"/>
          <ellipse cx="12" cy="12" rx="4" ry="10" transform="rotate(90 12 12)" stroke="#61DAFB" strokeWidth="1.5"/>
          <ellipse cx="12" cy="12" rx="4" ry="10" transform="rotate(150 12 12)" stroke="#61DAFB" strokeWidth="1.5"/>
          <circle cx="12" cy="12" r="1.8" fill="#61DAFB"/>
        </svg>
      );
    case 'postgresql':
    case 'postgres':
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 16.5h-2v-1.5h2v1.5zm3.07-4.25c-.37.38-.86.62-1.42.71v1.54h-1.3v-1.5c-.56-.09-1.05-.33-1.42-.71-.57-.59-.83-1.41-.83-2.39 0-.99.27-1.81.83-2.4.37-.38.86-.62 1.42-.71V7.26h1.3v1.54c.56.09 1.05.33 1.42.71.57.59.83 1.41.83 2.4 0 .98-.26 1.8-.83 2.39z" fill="#4169E1"/>
        </svg>
      );
    case 'fastapi':
      return <Zap size={size} color="#009688" className={className} />;
    case 'redis':
      return <Database size={size} color="#DC382D" className={className} />;
    case 'celery':
      return <Cpu size={size} color="#37814A" className={className} />;
    case 'monaco editor':
    case 'monaco':
      return <Code2 size={size} color="#007ACC" className={className} />;
    default:
      return <Server size={size} color="#6D45C5" className={className} />;
  }
}

export {
  Bug,
  ShieldCheck,
  ShieldAlert,
  Zap,
  Activity,
  Layers,
  FlaskConical,
  Database,
  Globe,
  Terminal,
  FileCode2,
  FileText,
  File,
  Folder,
  FolderOpen,
  Lock,
  Unlock,
  Search,
  SearchX,
  Trophy,
  Medal,
  Award,
  Crown,
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  ExternalLink,
  Eye,
  Users,
  UserX,
  BarChart3,
  Cpu,
  Server,
  Code2,
  GitCommit,
  GitPullRequest,
  Inbox,
  Sparkles,
  RotateCcw,
  Play,
  X,
};
