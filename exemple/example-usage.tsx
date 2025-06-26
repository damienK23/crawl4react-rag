/**
 * Example usage of the Hallucination Checker component for yogiz-flow
 * 
 * This shows how to integrate the hallucination checker into your React application.
 */

import React, { useState } from 'react';
import HallucinationChecker from './HallucinationChecker';
import { ComprehensiveReport } from './typescript-hallucination-detector';

const ExampleUsage: React.FC = () => {
  const [report, setReport] = useState<ComprehensiveReport | null>(null);
  const [showMarkdown, setShowMarkdown] = useState(false);

  // Example code with potential hallucinations
  const exampleCodeWithIssues = `import React, { useState, useWrongHook } from 'react';
import { nonExistentLibrary } from 'fake-package';

const MyComponent: React.FC = () => {
  const [count, setCount] = useState(0);
  
  // This hook doesn't exist
  const wrongHook = useWrongHook();
  
  // This method doesn't exist on React
  React.nonExistentMethod();
  
  // This is a valid React pattern
  React.useEffect(() => {
    console.log('Effect ran');
  }, []);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
    </div>
  );
};

export default MyComponent;`;

  const exampleGoodCode = `import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface User {
  id: number;
  name: string;
  email: string;
}

const UserList: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      try {
        const response = await axios.get<User[]>('/api/users');
        setUsers(response.data);
      } catch (error) {
        console.error('Failed to fetch users:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h2>Users</h2>
      <ul>
        {users.map(user => (
          <li key={user.id}>
            {user.name} - {user.email}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default UserList;`;

  const handleReportGenerated = (newReport: ComprehensiveReport) => {
    setReport(newReport);
    console.log('Hallucination report generated:', newReport);
  };

  const downloadReport = () => {
    if (!report) return;

    const dataStr = JSON.stringify(report, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `hallucination-report-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const copyMarkdown = () => {
    if (!report) return;

    const detector = new (require('./typescript-hallucination-detector').TSHallucinationDetector)();
    const markdown = detector.generateMarkdownReport(report);
    
    navigator.clipboard.writeText(markdown).then(() => {
      alert('Markdown report copied to clipboard!');
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🤖 AI Hallucination Detector for yogiz-flow
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Detect potential AI coding assistant hallucinations in your TypeScript/JavaScript code.
            This tool analyzes your code for non-existent methods, invalid imports, and other issues.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              🔴 Example with Issues
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              This code contains several hallucinations including non-existent hooks and methods.
            </p>
            <HallucinationChecker
              initialCode={exampleCodeWithIssues}
              language="typescript"
              onReportGenerated={handleReportGenerated}
            />
          </div>

          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              ✅ Example with Good Code
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              This code follows React best practices and should have minimal issues.
            </p>
            <HallucinationChecker
              initialCode={exampleGoodCode}
              language="typescript"
              onReportGenerated={handleReportGenerated}
            />
          </div>
        </div>

        {report && (
          <div className="bg-white rounded-lg shadow-sm border p-6 mb-8">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                📊 Latest Report Actions
              </h3>
              <div className="space-x-3">
                <button
                  onClick={downloadReport}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  📥 Download JSON
                </button>
                <button
                  onClick={copyMarkdown}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                >
                  📋 Copy Markdown
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {(report.validationSummary.overallConfidence * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">Confidence</div>
              </div>
              
              <div className="p-3 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {report.validationSummary.validCount}
                </div>
                <div className="text-sm text-gray-600">Valid Items</div>
              </div>
              
              <div className="p-3 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {report.hallucinationsDetected.length}
                </div>
                <div className="text-sm text-gray-600">Issues Found</div>
              </div>
              
              <div className="p-3 bg-yellow-50 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {(report.validationSummary.hallucinationRate * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">Issue Rate</div>
              </div>
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            🚀 Integration Instructions for yogiz-flow
          </h3>
          
          <div className="prose max-w-none">
            <h4 className="text-md font-semibold text-gray-800 mb-2">1. Install Dependencies</h4>
            <pre className="bg-gray-100 p-3 rounded-md text-sm overflow-x-auto mb-4">
              <code>{`npm install @babel/parser esprima`}</code>
            </pre>

            <h4 className="text-md font-semibold text-gray-800 mb-2">2. Import the Component</h4>
            <pre className="bg-gray-100 p-3 rounded-md text-sm overflow-x-auto mb-4">
              <code>{`import HallucinationChecker from './src/HallucinationChecker';
import { TSHallucinationDetector } from './src/typescript-hallucination-detector';`}</code>
            </pre>

            <h4 className="text-md font-semibold text-gray-800 mb-2">3. Use in Your Component</h4>
            <pre className="bg-gray-100 p-3 rounded-md text-sm overflow-x-auto mb-4">
              <code>{`const MyPage = () => {
  const handleReport = (report) => {
    // Process the hallucination report
    console.log('Analysis complete:', report);
  };

  return (
    <div>
      <HallucinationChecker
        language="typescript"
        onReportGenerated={handleReport}
      />
    </div>
  );
};`}</code>
            </pre>

            <h4 className="text-md font-semibold text-gray-800 mb-2">4. Features</h4>
            <ul className="list-disc pl-6 space-y-1 text-sm text-gray-700">
              <li>Real-time code analysis for TypeScript and JavaScript</li>
              <li>Detection of non-existent React hooks, methods, and functions</li>
              <li>Validation of imports and library usage</li>
              <li>Confidence scoring and severity assessment</li>
              <li>Exportable reports in JSON and Markdown formats</li>
              <li>Responsive UI with Tailwind CSS styling</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExampleUsage;