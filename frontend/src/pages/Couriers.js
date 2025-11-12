import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

export default function Couriers() {
  const [couriers, setCouriers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    fetchCouriers();
  }, [statusFilter]);

  const fetchCouriers = async () => {
    try {
      const params = statusFilter !== 'all' ? { status: statusFilter } : {};
      const response = await axios.get(`${API}/couriers`, { params });
      setCouriers(response.data.couriers);
    } catch (error) {
      console.error('Failed to fetch couriers:', error);
      toast.error('Failed to load couriers');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="couriers-container">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold text-gray-900" data-testid="couriers-title">Couriers</h1>
          <p className="text-gray-600 mt-1" data-testid="couriers-subtitle">Manage delivery couriers</p>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          data-testid="courier-status-filter"
        >
          <option value="all">All Status</option>
          <option value="online">Online</option>
          <option value="offline">Offline</option>
          <option value="busy">Busy</option>
          <option value="on_break">On Break</option>
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64" data-testid="couriers-loading">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : couriers.length === 0 ? (
        <div className="card text-center py-12" data-testid="no-couriers">
          <p className="text-gray-500 text-lg">No couriers found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="couriers-grid">
          {couriers.map((courier) => (
            <div key={courier.id} className="card" data-testid={`courier-card-${courier.id}`}>
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="font-bold text-lg text-gray-900 mb-1" data-testid={`courier-id-${courier.id}`}>
                    Courier #{courier.id.slice(0, 8)}
                  </h3>
                  <span className={`status-badge status-${courier.status}`} data-testid={`courier-status-${courier.id}`}>
                    {courier.status.toUpperCase()}
                  </span>
                </div>
                <div className="text-2xl">
                  {courier.vehicle_type === 'bicycle' && '🚴'}
                  {courier.vehicle_type === 'motorcycle' && '🏍️'}
                  {courier.vehicle_type === 'car' && '🚗'}
                  {courier.vehicle_type === 'van' && '🚚'}
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Vehicle:</span>
                  <span className="font-medium text-gray-900" data-testid={`courier-vehicle-${courier.id}`}>
                    {courier.vehicle_type.toUpperCase()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Rating:</span>
                  <span className="font-medium text-yellow-600" data-testid={`courier-rating-${courier.id}`}>
                    ⭐ {courier.rating?.toFixed(1) || '5.0'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Deliveries:</span>
                  <span className="font-medium text-gray-900" data-testid={`courier-deliveries-${courier.id}`}>
                    {courier.completed_deliveries || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Performance:</span>
                  <span className="font-medium text-green-600" data-testid={`courier-performance-${courier.id}`}>
                    {courier.performance_score?.toFixed(0) || 100}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Earnings:</span>
                  <span className="font-medium text-blue-600" data-testid={`courier-earnings-${courier.id}`}>
                    ${courier.total_earnings?.toFixed(2) || '0.00'}
                  </span>
                </div>
              </div>

              {courier.current_location && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <p className="text-xs text-gray-500" data-testid={`courier-location-${courier.id}`}>
                    📍 Current: {courier.current_location.lat?.toFixed(4)}, {courier.current_location.lng?.toFixed(4)}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
