import React, { useState, useEffect } from 'react';
import { supabase } from './supabase-client';

interface User {
    id: number;
    name: string;
    email: string;
    // Les colonnes réelles vs hallucinations seront testées
}

const DatabaseHallucinationTest = () => {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            // ❌ HALLUCINATION: Table qui n'existe probablement pas
            const { data: usersData } = await supabase
                .from('imaginary_users_table')
                .select('*');

            // ❌ HALLUCINATION: Colonnes qui n'existent probablement pas
            const { data: profilesData } = await supabase
                .from('profiles')
                .select(`
                    id,
                    username,
                    full_name,
                    avatar_url,
                    website,
                    biography,
                    social_media_links,
                    last_seen_at,
                    is_premium_member,
                    subscription_tier,
                    preferences_json,
                    metadata_blob,
                    custom_fields
                `);

            // ❌ HALLUCINATION: Fonction RPC qui n'existe probablement pas
            const { data: analytics } = await supabase
                .rpc('get_user_analytics_with_complex_calculations', {
                    user_id: 123,
                    date_range: '30d',
                    include_detailed_metrics: true,
                    aggregation_level: 'daily'
                });

            // ❌ HALLUCINATION: Fonction avec signature incorrecte
            const { data: permissions } = await supabase
                .rpc('check_user_permissions', {
                    user_uuid: 'some-uuid',
                    resource_type: 'document',
                    action_type: 'read',
                    context_data: { org_id: 456 }
                });

            // ❌ HALLUCINATION: Opération de base de données inexistante
            const { data: searchResults } = await supabase
                .from('documents')
                .select('*')
                .fullTextSearch('content', 'search term')  // Méthode inexistante
                .fuzzyMatch('title', 'approximate title')  // Méthode inexistante
                .semanticSimilarity('embeddings', [0.1, 0.2, 0.3]);  // Méthode inexistante

        } catch (error) {
            console.error('Database error:', error);
        }
    };

    const createUser = async (userData: any) => {
        try {
            // ❌ HALLUCINATION: Colonnes inexistantes dans l'insertion
            const { data, error } = await supabase
                .from('users')
                .insert({
                    username: userData.username,
                    email_address: userData.email,
                    password_hash: userData.password,
                    profile_picture_url: userData.avatar,
                    account_status: userData.status,
                    registration_source: userData.source,
                    email_verification_token: userData.token,
                    two_factor_secret: userData.twoFactor,
                    billing_address_json: userData.billing,
                    privacy_settings_blob: userData.privacy
                });

            // ❌ HALLUCINATION: Fonction de notification inexistante
            await supabase.rpc('send_welcome_email_with_template', {
                user_id: data[0].id,
                template_name: 'premium_welcome',
                personalization_data: {
                    first_name: userData.firstName,
                    subscription_type: 'premium'
                }
            });

        } catch (error) {
            console.error('User creation error:', error);
        }
    };

    const updateUserProfile = async (userId: number, updates: any) => {
        try {
            // ❌ HALLUCINATION: Colonnes de mise à jour inexistantes
            const { data, error } = await supabase
                .from('user_profiles')
                .update({
                    display_name: updates.displayName,
                    bio_description: updates.bio,
                    location_city: updates.city,
                    location_country: updates.country,
                    timezone_offset: updates.timezone,
                    language_preference: updates.language,
                    theme_settings: updates.theme,
                    notification_preferences: updates.notifications,
                    privacy_level: updates.privacy,
                    social_media_handles: updates.socialMedia
                })
                .eq('user_uuid', userId);  // ❌ Type de colonne incorrect (number vs uuid)

        } catch (error) {
            console.error('Profile update error:', error);
        }
    };

    const getAdvancedUserStats = async (userId: number) => {
        try {
            // ❌ HALLUCINATION: Procédure stockée complexe inexistante
            const { data } = await supabase.rpc('calculate_user_engagement_metrics', {
                user_id: userId,
                metrics_to_include: [
                    'daily_active_time',
                    'feature_usage_frequency',
                    'social_interaction_score',
                    'content_creation_rate',
                    'collaboration_index'
                ],
                time_period: {
                    start_date: '2024-01-01',
                    end_date: '2024-12-31',
                    granularity: 'weekly'
                },
                comparison_cohorts: ['power_users', 'new_users', 'inactive_users'],
                include_predictive_analytics: true
            });

            return data;
        } catch (error) {
            console.error('Stats calculation error:', error);
        }
    };

    const performComplexQuery = async () => {
        try {
            // ❌ HALLUCINATION: Requête avec jointures sur tables inexistantes
            const { data } = await supabase
                .from('user_activity_logs')
                .select(`
                    *,
                    user_profiles!inner (
                        display_name,
                        avatar_url,
                        subscription_tier
                    ),
                    activity_categories!inner (
                        category_name,
                        category_description,
                        point_value
                    ),
                    user_achievements (
                        achievement_name,
                        earned_at,
                        achievement_metadata
                    )
                `)
                .gte('activity_timestamp', '2024-01-01')
                .lte('activity_timestamp', '2024-12-31')
                .in('activity_type', ['login', 'content_creation', 'social_interaction'])
                .order('engagement_score', { ascending: false })  // ❌ Colonne inexistante
                .limit(100);

        } catch (error) {
            console.error('Complex query error:', error);
        }
    };

    // ❌ HALLUCINATION: Subscription en temps réel sur une table inexistante
    useEffect(() => {
        const subscription = supabase
            .channel('user_activity_stream')
            .on('postgres_changes', {
                event: '*',
                schema: 'public',
                table: 'real_time_user_activities',
                filter: `user_id=eq.${users[0]?.id}`
            }, (payload) => {
                console.log('Real-time update:', payload);
            })
            .subscribe();

        return () => {
            subscription.unsubscribe();
        };
    }, [users]);

    return (
        <div>
            <h1>Database Hallucination Test</h1>
            <p>Ce composant contient de nombreuses hallucinations de base de données:</p>
            <ul>
                <li>Tables inexistantes</li>
                <li>Colonnes inexistantes</li>
                <li>Fonctions RPC inexistantes</li>
                <li>Méthodes de requête inventées</li>
                <li>Types de données incorrects</li>
                <li>Signatures de fonction incorrectes</li>
            </ul>
            
            {loading ? (
                <p>Chargement...</p>
            ) : (
                <div>
                    {users.map(user => (
                        <div key={user.id}>
                            <h3>{user.name}</h3>
                            <p>{user.email}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default DatabaseHallucinationTest;