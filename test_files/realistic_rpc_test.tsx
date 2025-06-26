import React, { useState, useEffect } from 'react';
import { supabase } from './supabase-client';

interface UserAnalytics {
    user_id: string;
    metrics: any;
}

const RealisticRPCTest = () => {
    const [analytics, setAnalytics] = useState<UserAnalytics[]>([]);
    
    useEffect(() => {
        fetchUserAnalytics();
    }, []);

    const fetchUserAnalytics = async () => {
        try {
            // ✅ VALID: Correct RPC call with proper parameters
            const { data: validAnalytics } = await supabase
                .rpc('get_user_analytics_with_complex_calculations', {
                    user_id: '123e4567-e89b-12d3-a456-426614174000',
                    date_range: '30d',
                    include_detailed_metrics: true,
                    aggregation_level: 'daily',
                    filters: {
                        category: 'engagement',
                        min_score: 0.5
                    }
                });

            // ❌ INVALID: Wrong UUID format
            const { data: badUuid } = await supabase
                .rpc('get_user_analytics_with_complex_calculations', {
                    user_id: 'invalid-uuid-format',
                    date_range: '30d',
                    include_detailed_metrics: true,
                    aggregation_level: 'daily',
                    filters: {}
                });

            // ❌ INVALID: Wrong enum value
            const { data: badEnum } = await supabase
                .rpc('get_user_analytics_with_complex_calculations', {
                    user_id: '123e4567-e89b-12d3-a456-426614174000',
                    date_range: 'invalid_period', // Should be 7d, 30d, 90d, or 1y
                    include_detailed_metrics: true,
                    aggregation_level: 'hourly', // Should be daily, weekly, or monthly
                    filters: {}
                });

            // ❌ INVALID: Wrong type for boolean
            const { data: badBoolean } = await supabase
                .rpc('get_user_analytics_with_complex_calculations', {
                    user_id: '123e4567-e89b-12d3-a456-426614174000',
                    date_range: '30d',
                    include_detailed_metrics: 'yes', // Should be boolean
                    aggregation_level: 'daily',
                    filters: {}
                });

            // ❌ INVALID: Missing required parameters
            const { data: missingParams } = await supabase
                .rpc('get_user_analytics_with_complex_calculations', {
                    user_id: '123e4567-e89b-12d3-a456-426614174000'
                    // Missing: date_range, include_detailed_metrics, aggregation_level, filters
                });

            // ❌ INVALID: Extra unexpected parameters
            const { data: extraParams } = await supabase
                .rpc('get_user_analytics_with_complex_calculations', {
                    user_id: '123e4567-e89b-12d3-a456-426614174000',
                    date_range: '30d',
                    include_detailed_metrics: true,
                    aggregation_level: 'daily',
                    filters: {},
                    unexpected_param: 'should_not_be_here',
                    another_extra: 123
                });

            // ❌ INVALID: Wrong JSON structure
            const { data: badJson } = await supabase
                .rpc('get_user_analytics_with_complex_calculations', {
                    user_id: '123e4567-e89b-12d3-a456-426614174000',
                    date_range: '30d',
                    include_detailed_metrics: true,
                    aggregation_level: 'daily',
                    filters: 'not-a-json-object' // Should be object
                });

        } catch (error) {
            console.error('Analytics fetch error:', error);
        }
    };

    const checkPermissions = async (userId: string) => {
        try {
            // ✅ VALID: Proper permission check
            const { data: validPermission } = await supabase
                .rpc('check_user_permissions', {
                    user_uuid: '123e4567-e89b-12d3-a456-426614174000',
                    resource_type: 'document',
                    action_type: 'read',
                    context_data: { org_id: 456 }
                });

            // ❌ INVALID: Wrong enum for resource_type
            const { data: invalidResource } = await supabase
                .rpc('check_user_permissions', {
                    user_uuid: '123e4567-e89b-12d3-a456-426614174000',
                    resource_type: 'invalid_resource', // Should be document, project, user, or admin
                    action_type: 'read',
                    context_data: {}
                });

            // ❌ INVALID: Wrong type for user_uuid
            const { data: wrongType } = await supabase
                .rpc('check_user_permissions', {
                    user_uuid: 12345, // Should be UUID string
                    resource_type: 'document',
                    action_type: 'read'
                    // context_data is optional with default {}
                });

        } catch (error) {
            console.error('Permission check error:', error);
        }
    };

    const sendWelcomeEmail = async (newUserId: number) => {
        try {
            // ✅ VALID: Proper email sending
            const { data } = await supabase
                .rpc('send_welcome_email_with_template', {
                    user_id: 123,
                    template_name: 'premium_welcome',
                    personalization_data: {
                        first_name: 'John',
                        subscription_type: 'premium',
                        features: ['analytics', 'advanced_reports']
                    }
                });

            // ❌ INVALID: Wrong type for user_id  
            const { data: wrongUserId } = await supabase
                .rpc('send_welcome_email_with_template', {
                    user_id: 'not-a-number', // Should be bigint
                    template_name: 'welcome',
                    personalization_data: {}
                });

            // ❌ INVALID: Invalid JSON structure
            const { data: badPersonalization } = await supabase
                .rpc('send_welcome_email_with_template', {
                    user_id: 456,
                    template_name: 'welcome',
                    personalization_data: 'not-an-object' // Should be JSON object
                });

        } catch (error) {
            console.error('Email sending error:', error);
        }
    };

    return (
        <div>
            <h1>Realistic RPC Parameter Validation Test</h1>
            <p>This component contains realistic examples of:</p>
            <ul>
                <li>✅ Valid RPC calls with correct parameters</li>
                <li>❌ Invalid UUID formats</li>
                <li>❌ Invalid enum values</li>
                <li>❌ Wrong parameter types</li>
                <li>❌ Missing required parameters</li>
                <li>❌ Extra unexpected parameters</li>
                <li>❌ Invalid JSON structures</li>
            </ul>
            
            <div>
                <button onClick={() => fetchUserAnalytics()}>
                    Fetch Analytics
                </button>
                <button onClick={() => checkPermissions('test-user')}>
                    Check Permissions
                </button>
                <button onClick={() => sendWelcomeEmail(123)}>
                    Send Welcome Email
                </button>
            </div>
            
            <div>
                {analytics.map((item, index) => (
                    <div key={index}>
                        <p>User: {item.user_id}</p>
                        <pre>{JSON.stringify(item.metrics, null, 2)}</pre>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default RealisticRPCTest;