import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

export default function Analytics() {
  const [stats, setStats] = useState(null);
  const [revenue, setRevenue] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    fetchAnalytics();
  }, [days]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const [statsRes, revenueRes, performanceRes] = await Promise.all([
        axios.get(`${API}/analytics/orders/stats`, { params: { days } }),
        axios.get(`${API}/analytics/revenue`, { params: { days } }),
        axios.get(`${API}/analytics/couriers/performance`)
      ]);

      setStats(statsRes.data);
      setRevenue(revenueRes.data);
      setPerformance(performanceRes.data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="analytics-loading">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="analytics-container">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold text-gray-900" data-testid="analytics-title">Analytics</h1>
          <p className="text-gray-600 mt-1" data-testid="analytics-subtitle">Performance insights and metrics</p>
        </div>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          data-testid="period-filter"
        >
          <option value="7">Last 7 Days</option>
          <option value="30">Last 30 Days</option>
          <option value="90">Last 90 Days</option>
        </select>
      </div>

      {/* Revenue Analytics */}
      <div className="card bg-gradient-to-br from-green-50 to-emerald-100 border-green-200" data-testid="revenue-section">
        <h2 className="text-2xl font-bold text-green-900 mb-6">Revenue Analytics</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-green-700 mb-1">Total Revenue</p>
            <p className="text-3xl font-bold text-green-900" data-testid="total-revenue">
              ${revenue?.total_revenue?.toFixed(2) || '0.00'}
            </p>
          </div>
          <div>
            <p className="text-sm text-green-700 mb-1">Total Orders</p>
            <p className="text-3xl font-bold text-green-900" data-testid="total-revenue-orders">
              {revenue?.total_orders || 0}
            </p>
          </div>
          <div>
            <p className="text-sm text-green-700 mb-1">Average Order Value</p>
            <p className="text-3xl font-bold text-green-900" data-testid="avg-order-value">
              ${revenue?.average_order_value?.toFixed(2) || '0.00'}
            </p>
          </div>
        </div>
      </div>

      {/* Order Statistics */}
      <div className="card" data-testid="order-stats-section">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Order Statistics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 bg-blue-50 rounded-lg" data-testid="stat-total-orders">
            <p className="text-sm text-blue-700 mb-1">Total Orders</p>
            <p className="text-2xl font-bold text-blue-900">{stats?.total_orders || 0}</p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg" data-testid="stat-success-rate">
            <p className="text-sm text-green-700 mb-1">Success Rate</p>
            <p className="text-2xl font-bold text-green-900">{stats?.success_rate?.toFixed(1) || 0}%</p>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg" data-testid="stat-avg-delivery-time">
            <p className="text-sm text-purple-700 mb-1">Avg Delivery Time</p>
            <p className="text-2xl font-bold text-purple-900">{stats?.average_delivery_time_minutes?.toFixed(0) || 0} min</p>
          </div>
          <div className="p-4 bg-orange-50 rounded-lg" data-testid="stat-period">
            <p className="text-sm text-orange-700 mb-1">Period</p>
            <p className="text-2xl font-bold text-orange-900">{stats?.period_days || 0} days</p>
          </div>
        </div>

        {/* Status Breakdown */}
        {stats?.status_breakdown && (
          <div className="mt-6" data-testid="status-breakdown">
            <h3 className="font-semibold text-gray-900 mb-3">Status Breakdown</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {Object.entries(stats.status_breakdown).map(([status, count]) => (
                <div key={status} className="p-3 bg-gray-50 rounded-lg" data-testid={`status-${status}`}>
                  <p className="text-xs text-gray-600 mb-1">{status}</p>
                  <p className="text-xl font-bold text-gray-900">{count}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Top Performers */}
      <div className="card" data-testid="top-performers-section">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Top Performing Couriers</h2>
        <div className="space-y-3">
          {performance?.top_performers?.slice(0, 5).map((courier, index) => (
            <div
              key={courier.courier_id}
              className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-white rounded-lg border border-gray-200"
              data-testid={`top-courier-${index}`}
            >
              <div className="flex items-center space-x-4">
                <span className="text-2xl font-bold text-gray-400">#{index + 1}</span>
                <div>
                  <p className="font-semibold text-gray-900" data-testid={`top-courier-id-${index}`}>
                    Courier #{courier.courier_id.slice(0, 8)}
                  </p>
                  <p className="text-sm text-gray-600" data-testid={`top-courier-vehicle-${index}`}>
                    {courier.vehicle_type.toUpperCase()}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-6 text-sm">
                <div className="text-right">
                  <p className="text-gray-500">Performance</p>
                  <p className="font-semibold text-green-600" data-testid={`top-courier-score-${index}`}>
                    {courier.performance_score?.toFixed(0)}%
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-gray-500">Rating</p>
                  <p className="font-semibold text-yellow-600" data-testid={`top-courier-rating-${index}`}>
                    ⭐ {courier.rating?.toFixed(1)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-gray-500">Deliveries</p>
                  <p className="font-semibold text-blue-600" data-testid={`top-courier-deliveries-${index}`}>
                    {courier.completed_deliveries}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
