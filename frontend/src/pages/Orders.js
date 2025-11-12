import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchOrders();
  }, [filter]);

  const fetchOrders = async () => {
    try {
      const params = filter !== 'all' ? { status: filter } : {};
      const response = await axios.get(`${API}/orders`, { params });
      setOrders(response.data.orders);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
      toast.error('Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="orders-container">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold text-gray-900" data-testid="orders-title">Orders</h1>
          <p className="text-gray-600 mt-1" data-testid="orders-subtitle">Manage all delivery orders</p>
        </div>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          data-testid="status-filter"
        >
          <option value="all">All Status</option>
          <option value="created">Created</option>
          <option value="assigned">Assigned</option>
          <option value="picked">Picked</option>
          <option value="in_transit">In Transit</option>
          <option value="delivered">Delivered</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64" data-testid="orders-loading">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : orders.length === 0 ? (
        <div className="card text-center py-12" data-testid="no-orders">
          <p className="text-gray-500 text-lg">No orders found</p>
        </div>
      ) : (
        <div className="space-y-4" data-testid="orders-list">
          {orders.map((order) => (
            <div key={order.id} className="card hover:shadow-lg" data-testid={`order-card-${order.id}`}>
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-3">
                    <h3 className="font-bold text-lg" data-testid={`order-tracking-${order.id}`}>{order.tracking_code}</h3>
                    <span className={`status-badge status-${order.status}`} data-testid={`order-status-${order.id}`}>
                      {order.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500 font-medium">From:</p>
                      <p className="text-gray-900" data-testid={`order-pickup-${order.id}`}>
                        {order.pickup_address.street}, {order.pickup_address.city}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500 font-medium">To:</p>
                      <p className="text-gray-900" data-testid={`order-delivery-${order.id}`}>
                        {order.delivery_address.street}, {order.delivery_address.city}
                      </p>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center space-x-6 text-sm text-gray-600">
                    <span data-testid={`order-distance-${order.id}`}>📍 {order.estimated_distance?.toFixed(2)} km</span>
                    <span data-testid={`order-duration-${order.id}`}>⏱️ {order.estimated_duration?.toFixed(0)} mins</span>
                    <span className="font-semibold text-green-600" data-testid={`order-price-${order.id}`}>
                      ${order.estimated_price?.toFixed(2)}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500" data-testid={`order-created-${order.id}`}>
                    {new Date(order.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
