import React, { useState, useEffect } from 'react';
import { supabase } from './supabase-client';
import SomeNonExistentComponent from './nonexistent';

// Interface avec des problèmes
interface UserProps {
    name: string;
    age: number;
    // Propriété manquante pour les tests
}

// Composant avec de nombreux problèmes intentionnels
const userProfile = ({ userData, onUpdate, isLoading, theme, settings, config, debug, verbose, advanced, customProps }: UserProps) => {
    const [users, setUsers] = useState([]);
    const [count, setCount] = useState(0);
    
    // ❌ Hook conditionnel
    if (userData.length > 0) {
        const [extraState, setExtraState] = useState(false);
    }
    
    // ❌ Memory leak - pas de cleanup
    useEffect(() => {
        const timer = setTimeout(() => {
            console.log('Timer executed');
        }, 1000);
        
        const interval = setInterval(() => {
            console.log('Interval');
        }, 5000);
        
        // Event listener sans cleanup
        document.addEventListener('click', handleGlobalClick);
    }, []);
    
    // ❌ useEffect avec dépendances manquantes
    useEffect(() => {
        if (userData && userData.id) {
            fetchUserData(userData.id);
        }
    }, []); // userData manquant dans les dépendances
    
    const handleGlobalClick = () => {
        console.log('Global click');
    };
    
    const fetchUserData = async (userId: any) => {
        try {
            // ❌ Table Supabase qui n'existe probablement pas
            const { data } = await supabase
                .from('non_existent_users_table')
                .select('*')
                .eq('id', userId);
            
            // ❌ Fonction RPC qui n'existe probablement pas
            const { data: processedData } = await supabase
                .rpc('non_existent_function', { user_id: userId });
            
            setUsers(data);
        } catch (error) {
            console.error('Error:', error);
        }
    };
    
    // ❌ Mutation directe du state
    const handleAddUser = (newUser: any) => {
        users.push(newUser);
        setUsers(users);
    };
    
    // ❌ Signature de fonction incorrecte pour onClick
    const handleClick = (event: MouseEvent, extraParam: string, anotherParam: number) => {
        console.log('Clicked', event, extraParam, anotherParam);
    };
    
    // ❌ Usage de eval (sécurité)
    const processUserInput = (input: string) => {
        const result = eval(input); // Très dangereux !
        return result;
    };
    
    // ❌ Fonction avec trop de paramètres
    const complexFunction = (a: any, b: any, c: any, d: any, e: any, f: any, g: any, h: any, i: any, j: any, k: any) => {
        return a + b + c + d + e + f + g + h + i + j + k;
    };
    
    return (
        <div>
            <h1>User Profile</h1>
            
            {/* ❌ Image sans alt text */}
            <img src="/avatar.jpg" />
            
            {/* ❌ Button sans label accessible */}
            <button onClick={handleClick} />
            
            {/* ❌ Pas de key dans la liste */}
            {users.map(user => (
                <div onClick={() => handleClick(user)}> {/* ❌ Signature incorrecte */}
                    {user.name}
                </div>
            ))}
            
            {/* ❌ Inline object et function (performance) */}
            <SomeNonExistentComponent 
                style={{marginTop: 10, padding: 5}}
                onClick={() => console.log('inline function')}
                data={users}
            />
            
            {/* ❌ dangerouslySetInnerHTML (sécurité) */}
            <div dangerouslySetInnerHTML={{__html: userData.htmlContent}} />
            
            {/* ❌ Usage de this dans un composant fonctionnel */}
            <div onClick={() => this.handleSomething()}>
                Click me
            </div>
            
            {/* ❌ Hook dans une boucle */}
            {users.map(user => {
                const [userState, setUserState] = useState(user.data); // Hook dans map
                return <div key={user.id}>{userState}</div>;
            })}
        </div>
    );
};

// ❌ Composant non exporté
const UnusedComponent = () => {
    return <div>Never used</div>;
};

// ❌ Type any usage
const processData = (data: any): any => {
    return data.someProperty?.value!; // ❌ Non-null assertion
};

// ❌ Interface vide
interface EmptyInterface {
}

// ❌ Type alias inutilisé
type UnusedType = {
    field1: string;
    field2: number;
};

export default userProfile;