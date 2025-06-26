/**
 * React component for hallucination checking in yogiz-flow
 * 
 * This component provides a user interface for checking TypeScript/JavaScript code
 * for potential AI hallucinations and provides real-time feedback.
 */

import React, { useState, useCallback, useMemo } from 'react';
import { 
  TSHallucinationDetector, 
  ComprehensiveReport, 
  HallucinationReport,
  ValidationSummary 
} from './typescript-hallucination-detector';

interface HallucinationCheckerProps {
  initialCode?: string;
  language?: 'javascript' | 'typescript';
  onReportGenerated?: (report: ComprehensiveReport) => void;
  className?: string;
}

interface CheckResult {
  report: ComprehensiveReport | null;
  isChecking: boolean;
  error: string | null;
}

const HallucinationChecker: React.FC<HallucinationCheckerProps> = ({
  initialCode = '',
  language = 'typescript',
  onReportGenerated,
  className = ''
}) => {
  const [code, setCode] = useState(initialCode);
  const [result, setResult] = useState<CheckResult>({
    report: null,
    isChecking: false,
    error: null
  });

  const detector = useMemo(() => new TSHallucinationDetector(), []);

  const handleCheck = useCallback(async () => {
    if (!code.trim()) {
      setResult(prev => ({ ...prev, error: 'Please enter some code to check' }));
      return;
    }

    setResult(prev => ({ ...prev, isChecking: true, error: null }));

    try {
      // Simulate async operation for better UX
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const analysis = detector.analyzeCode(code, language);
      const report = detector.validateAnalysis(analysis);
      
      setResult({
        report,
        isChecking: false,
        error: null
      });

      if (onReportGenerated) {
        onReportGenerated(report);
      }
    } catch (error) {
      setResult({
        report: null,
        isChecking: false,
        error: error instanceof Error ? error.message : 'An error occurred during analysis'
      });
    }
  }, [code, language, detector, onReportGenerated]);

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-blue-600 bg-blue-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const renderSummary = (summary: ValidationSummary) => (
    <div className="bg-white rounded-lg shadow-sm border p-4 mb-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-3">Validation Summary</h3>
      
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className={`text-2xl font-bold ${getConfidenceColor(summary.overallConfidence)}`}>
            {(summary.overallConfidence * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-500">Confidence</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{summary.validCount}</div>
          <div className="text-sm text-gray-500">Valid</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">{summary.invalidCount + summary.notFoundCount}</div>
          <div className="text-sm text-gray-500">Issues</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-2 text-sm">
        <div className="flex justify-between">
          <span>Total:</span>
          <span className="font-medium">{summary.totalValidations}</span>
        </div>
        <div className="flex justify-between">
          <span>Valid:</span>
          <span className="font-medium text-green-600">{summary.validCount}</span>
        </div>
        <div className="flex justify-between">
          <span>Invalid:</span>
          <span className="font-medium text-red-600">{summary.invalidCount}</span>
        </div>
        <div className="flex justify-between">
          <span>Uncertain:</span>
          <span className="font-medium text-yellow-600">{summary.uncertainCount}</span>
        </div>
      </div>
    </div>
  );

  const renderHallucinations = (hallucinations: HallucinationReport[]) => (
    <div className="bg-white rounded-lg shadow-sm border p-4 mb-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-3">
        🚨 Potential Issues ({hallucinations.length})
      </h3>
      
      {hallucinations.length === 0 ? (
        <div className="text-green-600 text-sm">
          ✅ No obvious hallucinations detected!
        </div>
      ) : (
        <div className="space-y-3">
          {hallucinations.map((hallucination, index) => (
            <div 
              key={index}
              className={`p-3 rounded-md border-l-4 ${
                hallucination.severity === 'high' ? 'border-red-500' : 
                hallucination.severity === 'medium' ? 'border-yellow-500' : 
                'border-blue-500'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <div className="font-medium text-gray-900">
                  {hallucination.type.replace('_', ' ')}
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(hallucination.severity)}`}>
                  {hallucination.severity}
                </span>
              </div>
              
              <div className="text-sm text-gray-600 mb-1">
                📍 {hallucination.location}
              </div>
              
              <div className="text-sm text-gray-800 mb-2">
                {hallucination.description}
              </div>
              
              {hallucination.suggestion && (
                <div className="text-sm text-blue-600 bg-blue-50 p-2 rounded">
                  💡 {hallucination.suggestion}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderRecommendations = (recommendations: string[]) => (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-3">💡 Recommendations</h3>
      <ul className="space-y-2">
        {recommendations.map((rec, index) => (
          <li key={index} className="text-sm text-gray-700 flex items-start">
            <span className="text-blue-500 mr-2">•</span>
            {rec}
          </li>
        ))}
      </ul>
    </div>
  );

  return (
    <div className={`max-w-6xl mx-auto p-4 ${className}`}>
      <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          🤖 AI Hallucination Checker
        </h2>
        
        <div className="mb-4">
          <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-2">
            Language
          </label>
          <select 
            id="language"
            value={language}
            onChange={(e) => setCode('')}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="typescript">TypeScript</option>
            <option value="javascript">JavaScript</option>
          </select>
        </div>

        <div className="mb-4">
          <label htmlFor="code" className="block text-sm font-medium text-gray-700 mb-2">
            Code to Check
          </label>
          <textarea
            id="code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder={`Enter your ${language} code here...`}
            className="w-full h-64 border border-gray-300 rounded-md px-3 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex justify-between items-center">
          <button
            onClick={handleCheck}
            disabled={result.isChecking || !code.trim()}
            className={`px-4 py-2 rounded-md font-medium transition-colors ${
              result.isChecking || !code.trim()
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {result.isChecking ? 'Checking...' : 'Check for Hallucinations'}
          </button>

          {result.error && (
            <div className="text-red-600 text-sm">
              ❌ {result.error}
            </div>
          )}
        </div>
      </div>

      {result.report && (
        <div className="space-y-6">
          {renderSummary(result.report.validationSummary)}
          {renderHallucinations(result.report.hallucinationsDetected)}
          {renderRecommendations(result.report.recommendations)}
        </div>
      )}
    </div>
  );
};

export default HallucinationChecker;