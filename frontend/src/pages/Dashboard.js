import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardMetrics();
    const interval = setInterval(fetchDashboardMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardMetrics = async () => {
    try {
      const response = await axios.get(`${API}/analytics/dashboard`);
      setMetrics(response.data);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
      toast.error('Failed to load dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="dashboard-loading">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="dashboard-container">
      <div>
        <h1 className="text-4xl font-bold text-gray-900 mb-2" data-testid="dashboard-title">Dashboard</h1>
        <p className="text-gray-600" data-testid="dashboard-subtitle">Real-time logistics overview</p>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200" data-testid="metric-total-orders">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-blue-900">Total Orders</h3>
            <span className="text-2xl">📦</span>
          </div>
          <p className="text-3xl font-bold text-blue-700">{metrics?.total_orders || 0}</p>
        </div>

        <div className="card bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200" data-testid="metric-active-orders">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-orange-900">Active Orders</h3>
            <span className="text-2xl">🚚</span>
          </div>
          <p className="text-3xl font-bold text-orange-700">{metrics?.active_orders || 0}</p>
        </div>

        <div className="card bg-gradient-to-br from-green-50 to-green-100 border-green-200" data-testid="metric-completed-today">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-green-900">Completed Today</h3>
            <span className="text-2xl">✅</span>
          </div>
          <p className="text-3xl font-bold text-green-700">{metrics?.completed_today || 0}</p>
        </div>

        <div className="card bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200" data-testid="metric-online-couriers">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-purple-900">Online Couriers</h3>
            <span className="text-2xl">👥</span>
          </div>
          <p className="text-3xl font-bold text-purple-700">{metrics?.online_couriers || 0}</p>
        </div>
      </div>

      {/* Revenue Card */}
      <div className="card bg-gradient-to-br from-indigo-50 to-indigo-100 border-indigo-200" data-testid="revenue-card">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-indigo-900 mb-1">Total Revenue</h3>
            <p className="text-4xl font-bold text-indigo-700">${metrics?.total_revenue?.toFixed(2) || '0.00'}</p>
          </div>
          <span className="text-5xl">💰</span>
        </div>
      </div>

      {/* System Status */}
      <div className="card" data-testid="system-status">
        <h3 className="text-xl font-semibold mb-4">System Status</h3>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-gray-600">API Status</span>
            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">Operational</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Database</span>
            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">Connected</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Last Updated</span>
            <span className="text-sm text-gray-500">
              {metrics?.timestamp ? new Date(metrics.timestamp).toLocaleTimeString() : 'N/A'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
