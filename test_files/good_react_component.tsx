/**
 * Example of a good React TypeScript component for testing hallucination detection
 * This should have minimal issues and high confidence scores
 */

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

interface User {
  id: number;
  name: string;
  email: string;
}

interface UserListProps {
  onUserSelect?: (user: User) => void;
  className?: string;
}

const UserList: React.FC<UserListProps> = ({ onUserSelect, className }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get<User[]>('/api/users');
      setUsers(response.data);
    } catch (err) {
      console.error('Failed to fetch users:', err);
      setError('Failed to load users. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleUserClick = useCallback((user: User) => {
    onUserSelect?.(user);
  }, [onUserSelect]);

  if (loading) {
    return (
      <div className={`loading ${className || ''}`}>
        <p>Loading users...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`error ${className || ''}`}>
        <p>{error}</p>
        <button onClick={fetchUsers}>Retry</button>
      </div>
    );
  }

  return (
    <div className={`user-list ${className || ''}`}>
      <h2>Users</h2>
      {users.length === 0 ? (
        <p>No users found.</p>
      ) : (
        <ul>
          {users.map(user => (
            <li key={user.id} onClick={() => handleUserClick(user)}>
              <div className="user-info">
                <h3>{user.name}</h3>
                <p>{user.email}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default UserList;