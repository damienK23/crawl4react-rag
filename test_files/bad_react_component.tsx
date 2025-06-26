/**
 * Example of a React TypeScript component with hallucinations for testing
 * This should detect multiple issues and have low confidence scores
 */

import React, { useState, useEffect, useWrongHook, useFakeHook } from 'react';
import { nonExistentLibrary } from 'fake-react-package';
import axios from 'axios';
import { invalidModule } from '@fake/package';

interface User {
  id: number;
  name: string;
  email: string;
}

interface BadComponentProps {
  users?: User[];
  onSelect?: (user: User) => void;
}

const BadComponent: React.FC<BadComponentProps> = ({ users, onSelect }) => {
  const [data, setData] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  
  // These hooks don't exist in React
  const wrongHook = useWrongHook();
  const fakeHook = useFakeHook('some value');
  
  // This method doesn't exist on React
  React.nonExistentMethod();
  
  // Invalid lifecycle method in functional component
  const componentDidMount = () => {
    console.log('This is not how React functional components work');
  };

  useEffect(() => {
    // Invalid method call on axios
    axios.invalidMethod('/api/users')
      .then(response => {
        setData(response.data);
        
        // Non-existent array method
        const processedData = response.data.fakeFilter(item => item.id > 0);
        
        // Invalid console method
        console.invalidLog('Data processed:', processedData);
        
        // Invalid Object method
        Object.nonExistentMethod(processedData);
      })
      .catch(error => {
        // Invalid error handling
        error.nonExistentProperty = 'something';
        
        // Non-existent JSON method
        JSON.invalidStringify(error);
      });
  }, []);

  // Invalid event handler
  const handleInvalidEvent = (event) => {
    // Non-existent event methods
    event.nonExistentMethod();
    event.preventDefault.wrongCall();
  };

  // Invalid React patterns
  const renderUsers = () => {
    return data.fakeMap((user) => {
      return (
        <li key={user.id} onClick={() => {
          // Invalid user method
          user.nonExistentMethod();
          onSelect?.(user);
        }}>
          {user.name}
        </li>
      );
    });
  };

  // Using non-existent component
  return (
    <NonExistentWrapper>
      <div className="bad-component">
        <FakeHeader title="Users" />
        
        {loading && <InvalidSpinner />}
        
        <ul>
          {renderUsers()}
        </ul>
        
        <button onClick={handleInvalidEvent}>
          Invalid Button
        </button>
        
        {/* Using non-existent React feature */}
        <React.InvalidComponent data={data} />
      </div>
    </NonExistentWrapper>
  );
};

// Invalid export pattern
export { BadComponent as default, nonExistentExport };