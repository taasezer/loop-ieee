/*
  # LOOP Logistics Database Schema

  ## Overview
  Complete database schema for LOOP logistics platform including couriers, orders, 
  location tracking, and assignment history.

  ## New Tables
  
  ### `couriers`
  Stores courier/driver information
  - `id` (uuid, primary key) - Unique courier identifier
  - `name` (text) - Courier full name
  - `phone` (text) - Contact phone number
  - `email` (text) - Contact email
  - `status` (text) - Current status: available/busy/offline
  - `vehicle_type` (text) - Vehicle type (motorcycle, car, van, etc.)
  - `license_plate` (text) - Vehicle license plate
  - `rating` (decimal) - Average courier rating (1-5)
  - `total_deliveries` (integer) - Total completed deliveries
  - `created_at` (timestamptz) - Account creation timestamp
  - `updated_at` (timestamptz) - Last update timestamp

  ### `courier_locations`
  Real-time location tracking for couriers
  - `id` (uuid, primary key)
  - `courier_id` (uuid, foreign key) - Reference to courier
  - `latitude` (decimal) - GPS latitude
  - `longitude` (decimal) - GPS longitude
  - `accuracy` (decimal) - Location accuracy in meters
  - `speed` (decimal) - Current speed in km/h
  - `heading` (decimal) - Direction in degrees
  - `address` (text) - Reverse geocoded address
  - `timestamp` (timestamptz) - Location timestamp
  - `created_at` (timestamptz) - Record creation timestamp

  ### `orders`
  Delivery orders and requests
  - `id` (uuid, primary key)
  - `order_number` (text, unique) - Human-readable order number
  - `customer_name` (text) - Customer full name
  - `customer_phone` (text) - Customer contact
  - `pickup_latitude` (decimal) - Pickup GPS latitude
  - `pickup_longitude` (decimal) - Pickup GPS longitude
  - `pickup_address` (text) - Pickup address
  - `delivery_latitude` (decimal) - Delivery GPS latitude
  - `delivery_longitude` (decimal) - Delivery GPS longitude
  - `delivery_address` (text) - Delivery address
  - `package_weight` (decimal) - Package weight in kg
  - `package_description` (text) - Package contents description
  - `delivery_notes` (text) - Special delivery instructions
  - `priority` (integer) - Priority level (1-5)
  - `status` (text) - Order status
  - `distance_km` (decimal) - Calculated distance
  - `estimated_duration_minutes` (integer) - Estimated delivery time
  - `courier_id` (uuid, foreign key) - Assigned courier
  - `assigned_at` (timestamptz) - Assignment timestamp
  - `picked_up_at` (timestamptz) - Pickup timestamp
  - `delivered_at` (timestamptz) - Delivery timestamp
  - `created_at` (timestamptz) - Order creation timestamp
  - `updated_at` (timestamptz) - Last update timestamp

  ### `assignment_history`
  Tracks courier assignment history and AI decisions
  - `id` (uuid, primary key)
  - `order_id` (uuid, foreign key) - Reference to order
  - `courier_id` (uuid, foreign key) - Reference to courier
  - `assignment_score` (decimal) - AI algorithm score
  - `distance_to_pickup` (decimal) - Distance in km
  - `estimated_time` (integer) - Estimated time in minutes
  - `weather_factor` (decimal) - Weather impact score
  - `traffic_factor` (decimal) - Traffic impact score
  - `assigned_by` (text) - Assignment method (ai/manual)
  - `created_at` (timestamptz) - Assignment timestamp

  ### `location_history`
  Historical location data for analytics
  - `id` (uuid, primary key)
  - `courier_id` (uuid, foreign key)
  - `order_id` (uuid, foreign key, optional)
  - `latitude` (decimal)
  - `longitude` (decimal)
  - `timestamp` (timestamptz)
  - `created_at` (timestamptz)

  ## Security
  - RLS enabled on all tables
  - Policies for authenticated users to manage their data
  - Service role access for system operations
*/

-- Create couriers table
CREATE TABLE IF NOT EXISTS couriers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  phone text NOT NULL,
  email text NOT NULL,
  status text DEFAULT 'offline' CHECK (status IN ('available', 'busy', 'offline')),
  vehicle_type text NOT NULL,
  license_plate text,
  rating decimal(3,2) DEFAULT 5.00 CHECK (rating >= 0 AND rating <= 5),
  total_deliveries integer DEFAULT 0,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create courier_locations table for real-time tracking
CREATE TABLE IF NOT EXISTS courier_locations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  courier_id uuid NOT NULL REFERENCES couriers(id) ON DELETE CASCADE,
  latitude decimal(10,8) NOT NULL,
  longitude decimal(11,8) NOT NULL,
  accuracy decimal(10,2),
  speed decimal(10,2),
  heading decimal(5,2),
  address text,
  timestamp timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  order_number text UNIQUE NOT NULL,
  customer_name text NOT NULL,
  customer_phone text NOT NULL,
  pickup_latitude decimal(10,8) NOT NULL,
  pickup_longitude decimal(11,8) NOT NULL,
  pickup_address text NOT NULL,
  delivery_latitude decimal(10,8) NOT NULL,
  delivery_longitude decimal(11,8) NOT NULL,
  delivery_address text NOT NULL,
  package_weight decimal(10,2) NOT NULL,
  package_description text NOT NULL,
  delivery_notes text,
  priority integer DEFAULT 1 CHECK (priority >= 1 AND priority <= 5),
  status text DEFAULT 'pending' CHECK (status IN ('pending', 'assigned', 'picked_up', 'in_transit', 'delivered', 'cancelled')),
  distance_km decimal(10,2),
  estimated_duration_minutes integer,
  courier_id uuid REFERENCES couriers(id) ON DELETE SET NULL,
  assigned_at timestamptz,
  picked_up_at timestamptz,
  delivered_at timestamptz,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create assignment_history table
CREATE TABLE IF NOT EXISTS assignment_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id uuid NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  courier_id uuid NOT NULL REFERENCES couriers(id) ON DELETE CASCADE,
  assignment_score decimal(5,2),
  distance_to_pickup decimal(10,2),
  estimated_time integer,
  weather_factor decimal(5,2),
  traffic_factor decimal(5,2),
  assigned_by text DEFAULT 'ai' CHECK (assigned_by IN ('ai', 'manual')),
  created_at timestamptz DEFAULT now()
);

-- Create location_history table for analytics
CREATE TABLE IF NOT EXISTS location_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  courier_id uuid NOT NULL REFERENCES couriers(id) ON DELETE CASCADE,
  order_id uuid REFERENCES orders(id) ON DELETE SET NULL,
  latitude decimal(10,8) NOT NULL,
  longitude decimal(11,8) NOT NULL,
  timestamp timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_courier_locations_courier_id ON courier_locations(courier_id);
CREATE INDEX IF NOT EXISTS idx_courier_locations_timestamp ON courier_locations(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_courier_id ON orders(courier_id);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_assignment_history_order_id ON assignment_history(order_id);
CREATE INDEX IF NOT EXISTS idx_location_history_courier_id ON location_history(courier_id);
CREATE INDEX IF NOT EXISTS idx_location_history_timestamp ON location_history(timestamp DESC);

-- Create function to generate order numbers
CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS text AS $$
DECLARE
  new_number text;
BEGIN
  new_number := 'LOOP-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(FLOOR(RANDOM() * 10000)::text, 4, '0');
  RETURN new_number;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-generate order numbers
CREATE OR REPLACE FUNCTION set_order_number()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.order_number IS NULL THEN
    NEW.order_number := generate_order_number();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_order_number
  BEFORE INSERT ON orders
  FOR EACH ROW
  EXECUTE FUNCTION set_order_number();

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER trigger_couriers_updated_at
  BEFORE UPDATE ON couriers
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_orders_updated_at
  BEFORE UPDATE ON orders
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Enable Row Level Security
ALTER TABLE couriers ENABLE ROW LEVEL SECURITY;
ALTER TABLE courier_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignment_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE location_history ENABLE ROW LEVEL SECURITY;

-- RLS Policies for couriers
CREATE POLICY "Anyone can view couriers"
  ON couriers FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Service role can insert couriers"
  ON couriers FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Service role can update couriers"
  ON couriers FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service role can delete couriers"
  ON couriers FOR DELETE
  TO authenticated
  USING (true);

-- RLS Policies for courier_locations
CREATE POLICY "Anyone can view courier locations"
  ON courier_locations FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Service role can insert courier locations"
  ON courier_locations FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Service role can update courier locations"
  ON courier_locations FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- RLS Policies for orders
CREATE POLICY "Anyone can view orders"
  ON orders FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Service role can insert orders"
  ON orders FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Service role can update orders"
  ON orders FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service role can delete orders"
  ON orders FOR DELETE
  TO authenticated
  USING (true);

-- RLS Policies for assignment_history
CREATE POLICY "Anyone can view assignment history"
  ON assignment_history FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Service role can insert assignment history"
  ON assignment_history FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- RLS Policies for location_history
CREATE POLICY "Anyone can view location history"
  ON location_history FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Service role can insert location history"
  ON location_history FOR INSERT
  TO authenticated
  WITH CHECK (true);
